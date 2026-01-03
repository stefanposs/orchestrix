"""Account aggregate implementation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from orchestrix.core.aggregate import AggregateRoot
from orchestrix.core.event import Event

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

    def open(
        self, account_id: str, owner_name: str, initial_balance: Decimal
    ) -> None:
        """Open a new account."""
        if self.owner_name:
            msg = "Account already opened"
            raise ValueError(msg)

        if initial_balance < 0:
            msg = "Initial balance cannot be negative"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AccountOpened",
                AccountOpened(
                    account_id=account_id,
                    owner_name=owner_name,
                    initial_balance=initial_balance,
                    opened_at=now,
                ),
            )
        )

    def deposit(self, amount: Decimal, transaction_id: str, description: str) -> None:
        """Deposit money into the account."""
        self._validate_active()

        if amount <= 0:
            msg = "Deposit amount must be positive"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "MoneyDeposited",
                MoneyDeposited(
                    account_id=self.id,
                    amount=amount,
                    transaction_id=transaction_id,
                    description=description,
                    deposited_at=now,
                ),
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

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "MoneyWithdrawn",
                MoneyWithdrawn(
                    account_id=self.id,
                    amount=amount,
                    transaction_id=transaction_id,
                    description=description,
                    withdrawn_at=now,
                ),
            )
        )

    def suspend(self, reason: str) -> None:
        """Suspend the account."""
        if self.status != AccountStatus.ACTIVE:
            msg = f"Cannot suspend account in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AccountSuspended",
                AccountSuspended(
                    account_id=self.id, reason=reason, suspended_at=now
                ),
            )
        )

    def reactivate(self) -> None:
        """Reactivate a suspended account."""
        if self.status != AccountStatus.SUSPENDED:
            msg = f"Cannot reactivate account in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AccountReactivated",
                AccountReactivated(account_id=self.id, reactivated_at=now),
            )
        )

    def close(self) -> None:
        """Close the account."""
        self._validate_active()

        if self.balance != 0:
            msg = f"Cannot close account with non-zero balance: {self.balance}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AccountClosed",
                AccountClosed(
                    account_id=self.id, final_balance=self.balance, closed_at=now
                ),
            )
        )

    def _validate_active(self) -> None:
        """Validate account is active."""
        if self.status != AccountStatus.ACTIVE:
            msg = f"Account is {self.status}, not active"
            raise ValueError(msg)

    # Event handlers

    def _when_account_opened(self, event: Event) -> None:
        """Apply AccountOpened event."""
        data = event.data
        self.id = data.account_id
        self.owner_name = data.owner_name
        self.balance = data.initial_balance
        self.status = AccountStatus.ACTIVE
        self.opened_at = data.opened_at

    def _when_money_deposited(self, event: Event) -> None:
        """Apply MoneyDeposited event."""
        data = event.data
        self.balance += data.amount
        self.transactions.append(data.transaction_id)

    def _when_money_withdrawn(self, event: Event) -> None:
        """Apply MoneyWithdrawn event."""
        data = event.data
        self.balance -= data.amount
        self.transactions.append(data.transaction_id)

    def _when_account_suspended(self, _event: Event) -> None:
        """Apply AccountSuspended event."""
        self.status = AccountStatus.SUSPENDED

    def _when_account_reactivated(self, _event: Event) -> None:
        """Apply AccountReactivated event."""
        self.status = AccountStatus.ACTIVE

    def _when_account_closed(self, _event: Event) -> None:
        """Apply AccountClosed event."""
        self.status = AccountStatus.CLOSED
