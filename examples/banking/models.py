"""Domain models for the banking example."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


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


@dataclass(frozen=True)
class AccountOpened:
    """Account was opened."""

    account_id: str
    owner_name: str
    initial_balance: Decimal
    opened_at: datetime


@dataclass(frozen=True)
class MoneyDeposited:
    """Money was deposited into account."""

    account_id: str
    amount: Decimal
    transaction_id: str
    description: str
    deposited_at: datetime


@dataclass(frozen=True)
class MoneyWithdrawn:
    """Money was withdrawn from account."""

    account_id: str
    amount: Decimal
    transaction_id: str
    description: str
    withdrawn_at: datetime


@dataclass(frozen=True)
class AccountSuspended:
    """Account was suspended."""

    account_id: str
    reason: str
    suspended_at: datetime


@dataclass(frozen=True)
class AccountReactivated:
    """Account was reactivated."""

    account_id: str
    reactivated_at: datetime


@dataclass(frozen=True)
class AccountClosed:
    """Account was closed."""

    account_id: str
    final_balance: Decimal
    closed_at: datetime


@dataclass(frozen=True)
class TransferInitiated:
    """Transfer between accounts was started."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: str
    initiated_at: datetime


@dataclass(frozen=True)
class TransferDebited:
    """Money was debited from source account."""

    transfer_id: str
    from_account_id: str
    amount: Decimal
    debited_at: datetime


@dataclass(frozen=True)
class TransferCompleted:
    """Transfer was completed successfully."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    completed_at: datetime


@dataclass(frozen=True)
class TransferFailed:
    """Transfer failed."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    reason: str
    failed_at: datetime


@dataclass(frozen=True)
class TransferReversed:
    """Transfer was reversed (compensation)."""

    transfer_id: str
    from_account_id: str
    amount: Decimal
    reversed_at: datetime


# Commands


@dataclass(frozen=True)
class OpenAccount:
    """Open a new account."""

    account_id: str
    owner_name: str
    initial_balance: Decimal


@dataclass(frozen=True)
class DepositMoney:
    """Deposit money into an account."""

    account_id: str
    amount: Decimal
    description: str


@dataclass(frozen=True)
class WithdrawMoney:
    """Withdraw money from an account."""

    account_id: str
    amount: Decimal
    description: str


@dataclass(frozen=True)
class TransferMoney:
    """Transfer money between accounts."""

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: str


@dataclass(frozen=True)
class SuspendAccount:
    """Suspend an account."""

    account_id: str
    reason: str


@dataclass(frozen=True)
class ReactivateAccount:
    """Reactivate a suspended account."""

    account_id: str


@dataclass(frozen=True)
class CloseAccount:
    """Close an account."""

    account_id: str
