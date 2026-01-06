"""Transfer saga coordinating money transfers between accounts.

This saga implements the two-phase commit pattern:
1. Debit from source account
2. Credit to destination account
3. If step 2 fails, reverse step 1 (compensation)
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.core.messaging import AsyncMessageBus

from .aggregate import Account
from .models import (
    DepositMoney,
    TransferCompleted,
    TransferDebited,
    TransferFailed,
    TransferInitiated,
    TransferReversed,
    WithdrawMoney,
)


@dataclass
class TransferSaga:
    """Saga coordinating money transfers with compensation."""

    message_bus: AsyncMessageBus
    repository: AggregateRepository[Account]

    async def handle_transfer_initiated(self, event: TransferInitiated) -> None:
        """Start transfer by debiting source account."""
        try:
            # Withdraw from source account
            await self.message_bus.publish(
                WithdrawMoney(
                    account_id=event.from_account_id,
                    amount=event.amount,
                    description=f"Transfer {event.transfer_id}: {event.description}",
                )
            )

            # Record debit
            now = datetime.now(UTC)
            await self.message_bus.publish(
                TransferDebited(
                    transfer_id=event.transfer_id,
                    from_account_id=event.from_account_id,
                    amount=event.amount,
                    debited_at=now,
                )
            )
        except Exception as e:
            # Withdrawal failed (insufficient funds, suspended account, etc.)
            now = datetime.now(UTC)
            await self.message_bus.publish(
                TransferFailed(
                    transfer_id=event.transfer_id,
                    from_account_id=event.from_account_id,
                    to_account_id=event.to_account_id,
                    amount=event.amount,
                    reason=str(e),
                    failed_at=now,
                )
            )

    async def handle_transfer_debited(self, event: TransferDebited) -> None:
        """Complete transfer by crediting destination account."""
        # Find the original transfer info
        # In production, you'd store transfer state or query from event store
        # For this example, we'll get it from the context
        transfer_event = None
        # Note: accessing event_store directly and assuming async capability
        # In a real app, we'd use a proper interface
        events = await self.repository.event_store.load(f"transfer-{event.transfer_id}")  # type: ignore
        for evt in events:
            if evt.type == "TransferInitiated":
                transfer_event = evt
                break

        if not transfer_event:
            return  # Cannot proceed without transfer info

        transfer_data: TransferInitiated = transfer_event

        try:
            # Deposit to destination account
            await self.message_bus.publish(
                DepositMoney(
                    account_id=transfer_data.to_account_id,
                    amount=event.amount,
                    description=f"Transfer {event.transfer_id}: {transfer_data.description}",
                )
            )

            # Mark transfer as completed
            now = datetime.now(UTC)
            await self.message_bus.publish(
                TransferCompleted(
                    transfer_id=event.transfer_id,
                    from_account_id=event.from_account_id,
                    to_account_id=transfer_data.to_account_id,
                    amount=event.amount,
                    completed_at=now,
                )
            )
        except Exception as e:
            # Deposit failed - need to compensate by reversing withdrawal
            # Re-deposit to source account
            await self.message_bus.publish(
                DepositMoney(
                    account_id=event.from_account_id,
                    amount=event.amount,
                    description=f"Transfer {event.transfer_id} reversal",
                )
            )

            # Mark transfer as reversed
            now = datetime.now(UTC)
            await self.message_bus.publish(
                TransferReversed(
                    transfer_id=event.transfer_id,
                    from_account_id=event.from_account_id,
                    amount=event.amount,
                    reversed_at=now,
                )
            )

            # Also mark as failed
            await self.message_bus.publish(
                TransferFailed(
                    transfer_id=event.transfer_id,
                    from_account_id=event.from_account_id,
                    to_account_id=transfer_data.to_account_id,
                    amount=event.amount,
                    reason=f"Deposit failed: {e}. Transfer reversed.",
                    failed_at=now,
                )
            )


def register_saga(
    message_bus: AsyncMessageBus, repository: AggregateRepository[Account]
) -> TransferSaga:
    """Register saga event handlers with the message bus."""
    saga = TransferSaga(message_bus=message_bus, repository=repository)

    # Subscribe to domain events
    message_bus.subscribe(TransferInitiated, saga.handle_transfer_initiated)
    message_bus.subscribe(TransferDebited, saga.handle_transfer_debited)

    return saga
