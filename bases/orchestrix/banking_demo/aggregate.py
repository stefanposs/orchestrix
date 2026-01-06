"""Account aggregate implementation."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from orchestrix.core.eventsourcing.aggregate import AggregateRoot

from .models import (
    AccountClosed,
    AccountOpened,
    AccountReactivated,
    AccountStatus,
    AccountSuspended,
    MoneyDeposited,
    MoneyWithdrawn,
)


@dataclass
class Account(AggregateRoot):
    """Account aggregate managing balance and transactions."""

    owner_name: str = ""
    balance: Decimal = Decimal("0.00")
    status: AccountStatus = AccountStatus.ACTIVE
    opened_at: datetime | None = None
    transactions: list[str] = field(default_factory=list)

    def open(self, account_id: str, owner_name: str, initial_balance: Decimal) -> None:
        """Open a new account."""
        if self.owner_name:
            msg = "Account already opened"
            raise ValueError(msg)

        if initial_balance < 0:
            msg = "Initial balance cannot be negative"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AccountOpened(
                account_id=account_id,
                owner_name=owner_name,
                initial_balance=initial_balance,
                opened_at=now,
            )
        )

    def deposit(self, amount: Decimal, transaction_id: str, description: str) -> None:
        """Deposit money into the account."""
        self._validate_active()

        if amount <= 0:
            msg = "Deposit amount must be positive"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            MoneyDeposited(
                account_id=self.aggregate_id,
                amount=amount,
                transaction_id=transaction_id,
                description=description,
                deposited_at=now,
            )
        )

    def withdraw(self, amount: Decimal, transaction_id: str, description: str) -> None:
        """Withdraw money from the account."""
        self._validate_active()

        if amount <= 0:
            msg = "Withdrawal amount must be positive"
            raise ValueError(msg)

        if self.balance < amount:
            msg = f"Insufficient balance: {self.balance} < {amount}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            MoneyWithdrawn(
                account_id=self.aggregate_id,
                amount=amount,
                transaction_id=transaction_id,
                description=description,
                withdrawn_at=now,
            )
        )

    def suspend(self, reason: str) -> None:
        """Suspend the account."""
        if self.status != AccountStatus.ACTIVE:
            msg = f"Cannot suspend account in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AccountSuspended(
                account_id=self.aggregate_id,
                reason=reason,
                suspended_at=now,
            )
        )

    def reactivate(self) -> None:
        """Reactivate a suspended account."""
        if self.status != AccountStatus.SUSPENDED:
            msg = f"Cannot reactivate account in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AccountReactivated(
                account_id=self.aggregate_id,
                reactivated_at=now,
            )
        )

    def close(self) -> None:
        """Close the account."""
        self._validate_active()

        if self.balance != 0:
            msg = f"Cannot close account with non-zero balance: {self.balance}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AccountClosed(
                account_id=self.aggregate_id,
                final_balance=self.balance,
                closed_at=now,
            )
        )

    def _validate_active(self) -> None:
        """Validate account is active."""
        if self.status != AccountStatus.ACTIVE:
            msg = f"Account is {self.status}, not active"
            raise ValueError(msg)

    # Event handlers

    def _when_account_opened(self, event: AccountOpened) -> None:
        """Apply AccountOpened event."""
        self.aggregate_id = event.account_id
        self.owner_name = event.owner_name
        self.balance = event.initial_balance
        self.status = AccountStatus.ACTIVE
        self.opened_at = event.opened_at

    def _when_money_deposited(self, event: MoneyDeposited) -> None:
        """Apply MoneyDeposited event."""
        self.balance += event.amount
        self.transactions.append(event.transaction_id)

    def _when_money_withdrawn(self, event: MoneyWithdrawn) -> None:
        """Apply MoneyWithdrawn event."""
        self.balance -= event.amount
        self.transactions.append(event.transaction_id)

    def _when_account_suspended(self, _event: AccountSuspended) -> None:
        """Apply AccountSuspended event."""
        self.status = AccountStatus.SUSPENDED

    def _when_account_reactivated(self, _event: AccountReactivated) -> None:
        """Apply AccountReactivated event."""
        self.status = AccountStatus.ACTIVE

    def _when_account_closed(self, _event: AccountClosed) -> None:
        """Apply AccountClosed event."""
        self.status = AccountStatus.CLOSED
