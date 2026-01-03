"""Domain models for the banking example."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from orchestrix.core.message import Command, Event


class AccountStatus(str, Enum):
    """Account lifecycle states."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class TransferStatus(str, Enum):
    """Transfer processing states."""

    PENDING = "pending"
    DEBITED = "debited"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


# Events


@dataclass(frozen=True, kw_only=True)
class AccountOpened(Event):
    """Account was opened."""

    account_id: str
    owner_name: str
    initial_balance: Decimal
    opened_at: datetime


@dataclass(frozen=True, kw_only=True)
class MoneyDeposited(Event):
    """Money was deposited into account."""

    account_id: str
    amount: Decimal
    transaction_id: str
    description: str
    deposited_at: datetime


@dataclass(frozen=True, kw_only=True)
class MoneyWithdrawn(Event):
    """Money was withdrawn from account."""

    account_id: str
    amount: Decimal
    transaction_id: str
    description: str
    withdrawn_at: datetime


@dataclass(frozen=True, kw_only=True)
class AccountSuspended(Event):
    """Account was suspended."""

    account_id: str
    reason: str
    suspended_at: datetime


@dataclass(frozen=True, kw_only=True)
class AccountReactivated(Event):
    """Account was reactivated."""

    account_id: str
    reactivated_at: datetime


@dataclass(frozen=True, kw_only=True)
class AccountClosed(Event):
    """Account was closed."""

    account_id: str
    final_balance: Decimal
    closed_at: datetime


@dataclass(frozen=True, kw_only=True)
class TransferInitiated(Event):
    """Transfer between accounts was started."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: str
    initiated_at: datetime


@dataclass(frozen=True, kw_only=True)
class TransferDebited(Event):
    """Money was debited from source account."""

    transfer_id: str
    from_account_id: str
    amount: Decimal
    debited_at: datetime


@dataclass(frozen=True, kw_only=True)
class TransferCompleted(Event):
    """Transfer was completed successfully."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    completed_at: datetime


@dataclass(frozen=True, kw_only=True)
class TransferFailed(Event):
    """Transfer failed."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    reason: str
    failed_at: datetime


@dataclass(frozen=True, kw_only=True)
class TransferReversed(Event):
    """Transfer was reversed (compensation)."""

    transfer_id: str
    from_account_id: str
    amount: Decimal
    reversed_at: datetime


# Commands


@dataclass(frozen=True, kw_only=True)
class OpenAccount(Command):
    """Open a new account."""

    account_id: str
    owner_name: str
    initial_balance: Decimal


@dataclass(frozen=True, kw_only=True)
class DepositMoney(Command):
    """Deposit money into an account."""

    account_id: str
    amount: Decimal
    description: str


@dataclass(frozen=True, kw_only=True)
class WithdrawMoney(Command):
    """Withdraw money from an account."""

    account_id: str
    amount: Decimal
    description: str


@dataclass(frozen=True, kw_only=True)
class TransferMoney(Command):
    """Transfer money between accounts."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: str


@dataclass(frozen=True, kw_only=True)
class SuspendAccount(Command):
    """Suspend an account."""

    account_id: str
    reason: str


@dataclass(frozen=True, kw_only=True)
class ReactivateAccount(Command):
    """Reactivate a suspended account."""

    account_id: str


@dataclass(frozen=True, kw_only=True)
class CloseAccount(Command):
    """Close an account."""

    account_id: str
