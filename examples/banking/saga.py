"""Transfer saga coordinating money transfers between accounts.

This saga implements the two-phase commit pattern:
1. Debit from source account
2. Credit to destination account
3. If step 2 fails, reverse step 1 (compensation)
"""
from dataclasses import dataclass
from datetime import datetime, timezone

from orchestrix.core.aggregate import AggregateRepository
from orchestrix.core.event import Event
from orchestrix.core.messaging import MessageBus

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

    message_bus: MessageBus
    repository: AggregateRepository

    async def handle_transfer_initiated(self, event: Event) -> None:
        """Start transfer by debiting source account."""
        data: TransferInitiated = event.data

        try:
            # Withdraw from source account
            await self.message_bus.publish_async(
                WithdrawMoney(
                    account_id=data.from_account_id,
                    amount=data.amount,
                    description=f"Transfer {data.transfer_id}: {data.description}",
                )
            )

            # Record debit
            now = datetime.now(timezone.utc)
            await self.message_bus.publish_async(
                TransferDebited(
                    transfer_id=data.transfer_id,
                    from_account_id=data.from_account_id,
                    amount=data.amount,
                    debited_at=now,
                )
            )
        except Exception as e:
            # Withdrawal failed (insufficient funds, suspended account, etc.)
            now = datetime.now(timezone.utc)
            await self.message_bus.publish_async(
                TransferFailed(
                    transfer_id=data.transfer_id,
                    from_account_id=data.from_account_id,
                    to_account_id=data.to_account_id,
                    amount=data.amount,
                    reason=str(e),
                    failed_at=now,
                )
            )

    async def handle_transfer_debited(self, event: Event) -> None:
        """Complete transfer by crediting destination account."""
        data: TransferDebited = event.data

        # Find the original transfer info
        # In production, you'd store transfer state or query from event store
        # For this example, we'll get it from the context
        transfer_event = None
        events = await self.repository.event_store.load_async(
            f"transfer-{data.transfer_id}"
        )
        for evt in events:
            if evt.type == "TransferInitiated":
                transfer_event = evt
                break

        if not transfer_event:
            return  # Cannot proceed without transfer info

        transfer_data: TransferInitiated = transfer_event.data

        try:
            # Deposit to destination account
            await self.message_bus.publish_async(
                DepositMoney(
                    account_id=transfer_data.to_account_id,
                    amount=data.amount,
                    description=f"Transfer {data.transfer_id}: {transfer_data.description}",
                )
            )

            # Mark transfer as completed
            now = datetime.now(timezone.utc)
            await self.message_bus.publish_async(
                TransferCompleted(
                    transfer_id=data.transfer_id,
                    from_account_id=data.from_account_id,
                    to_account_id=transfer_data.to_account_id,
                    amount=data.amount,
                    completed_at=now,
                )
            )
        except Exception as e:
            # Deposit failed - need to compensate by reversing withdrawal
            # Re-deposit to source account
            await self.message_bus.publish_async(
                DepositMoney(
                    account_id=data.from_account_id,
                    amount=data.amount,
                    description=f"Transfer {data.transfer_id} reversal",
                )
            )

            # Mark transfer as reversed
            now = datetime.now(timezone.utc)
            await self.message_bus.publish_async(
                TransferReversed(
                    transfer_id=data.transfer_id,
                    from_account_id=data.from_account_id,
                    amount=data.amount,
                    reversed_at=now,
                )
            )

            # Also mark as failed
            await self.message_bus.publish_async(
                TransferFailed(
                    transfer_id=data.transfer_id,
                    from_account_id=data.from_account_id,
                    to_account_id=transfer_data.to_account_id,
                    amount=data.amount,
                    reason=f"Deposit failed: {e}. Transfer reversed.",
                    failed_at=now,
                )
            )


def register_saga(
    message_bus: MessageBus, repository: AggregateRepository
) -> TransferSaga:
    """Register saga event handlers with the message bus."""
    saga = TransferSaga(message_bus=message_bus, repository=repository)

    # Subscribe to domain events
    message_bus.subscribe(TransferInitiated, saga.handle_transfer_initiated)
    message_bus.subscribe(TransferDebited, saga.handle_transfer_debited)

    return saga
