"""Command handlers for banking operations."""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from orchestrix.core.aggregate import AggregateRepository
from orchestrix.core.messaging import MessageBus

from .aggregate import Account
from .models import (
    CloseAccount,
    DepositMoney,
    OpenAccount,
    ReactivateAccount,
    SuspendAccount,
    TransferInitiated,
    TransferMoney,
    WithdrawMoney,
)


@dataclass
class BankingCommandHandlers:
    """Handlers for banking commands."""

    repository: AggregateRepository
    message_bus: MessageBus

    async def handle_open_account(self, command: OpenAccount) -> None:
        """Open a new account."""
        account = Account()
        account.open(
            account_id=command.account_id,
            owner_name=command.owner_name,
            initial_balance=command.initial_balance,
        )

        await self.repository.save_async(account)

        # Publish events
        for event in account.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_deposit_money(self, command: DepositMoney) -> None:
        """Deposit money into an account."""
        account = await self.repository.load_async(Account, command.account_id)

        transaction_id = str(uuid4())
        account.deposit(
            amount=command.amount,
            transaction_id=transaction_id,
            description=command.description,
        )

        await self.repository.save_async(account)

        # Publish events
        for event in account.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_withdraw_money(self, command: WithdrawMoney) -> None:
        """Withdraw money from an account."""
        account = await self.repository.load_async(Account, command.account_id)

        transaction_id = str(uuid4())
        account.withdraw(
            amount=command.amount,
            transaction_id=transaction_id,
            description=command.description,
        )

        await self.repository.save_async(account)

        # Publish events
        for event in account.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_transfer_money(self, command: TransferMoney) -> None:
        """Initiate a money transfer (saga will handle the workflow)."""
        # Just publish the TransferInitiated event
        # The saga will coordinate the actual transfer
        now = datetime.now(timezone.utc)
        await self.message_bus.publish_async(
            TransferInitiated(
                transfer_id=command.transfer_id,
                from_account_id=command.from_account_id,
                to_account_id=command.to_account_id,
                amount=command.amount,
                description=command.description,
                initiated_at=now,
            )
        )

    async def handle_suspend_account(self, command: SuspendAccount) -> None:
        """Suspend an account."""
        account = await self.repository.load_async(Account, command.account_id)

        account.suspend(reason=command.reason)

        await self.repository.save_async(account)

        # Publish events
        for event in account.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_reactivate_account(self, command: ReactivateAccount) -> None:
        """Reactivate a suspended account."""
        account = await self.repository.load_async(Account, command.account_id)

        account.reactivate()

        await self.repository.save_async(account)

        # Publish events
        for event in account.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_close_account(self, command: CloseAccount) -> None:
        """Close an account."""
        account = await self.repository.load_async(Account, command.account_id)

        account.close()

        await self.repository.save_async(account)

        # Publish events
        for event in account.uncommitted_events:
            await self.message_bus.publish_async(event.data)


def register_handlers(
    message_bus: MessageBus, repository: AggregateRepository
) -> BankingCommandHandlers:
    """Register command handlers with the message bus."""
    handlers = BankingCommandHandlers(repository=repository, message_bus=message_bus)

    # Subscribe to commands
    message_bus.subscribe(OpenAccount, handlers.handle_open_account)
    message_bus.subscribe(DepositMoney, handlers.handle_deposit_money)
    message_bus.subscribe(WithdrawMoney, handlers.handle_withdraw_money)
    message_bus.subscribe(TransferMoney, handlers.handle_transfer_money)
    message_bus.subscribe(SuspendAccount, handlers.handle_suspend_account)
    message_bus.subscribe(ReactivateAccount, handlers.handle_reactivate_account)
    message_bus.subscribe(CloseAccount, handlers.handle_close_account)

    return handlers
