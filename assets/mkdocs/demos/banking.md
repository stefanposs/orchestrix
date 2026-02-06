
# Banking Demo — Money Transfers with Compensation

Event-sourced account management with two-phase transfers, saga-based
compensation, and a full transaction audit trail.

> **Source Code:**
> [`bases/orchestrix/banking_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/banking_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.banking_demo.main
```

## What It Demonstrates

- **Event-sourced accounts** — balance reconstructed from events
- **Transfer saga** — two-phase debit/credit with automatic rollback
- **Compensation** — if the credit leg fails, the debit is reversed
- **Account lifecycle** — open, suspend, reactivate, close
- **Command handlers** — `BankingCommandHandlers` wires everything together

## Domain Model

### Commands

| Command | Fields | Description |
|---|---|---|
| `OpenAccount` | `account_id`, `owner_name`, `initial_balance` | Open a new account |
| `DepositMoney` | `account_id`, `amount`, `description` | Deposit funds |
| `WithdrawMoney` | `account_id`, `amount`, `description` | Withdraw funds |
| `TransferMoney` | `transfer_id`, `from_account_id`, `to_account_id`, `amount`, `description` | Transfer between accounts |
| `SuspendAccount` | `account_id`, `reason` | Suspend an account |
| `ReactivateAccount` | `account_id` | Reactivate a suspended account |
| `CloseAccount` | `account_id` | Close an account |

### Events

| Event | Description |
|---|---|
| `AccountOpened` | Account created with initial balance |
| `MoneyDeposited` | Funds added |
| `MoneyWithdrawn` | Funds removed |
| `AccountSuspended` | Account suspended |
| `AccountReactivated` | Account reactivated |
| `AccountClosed` | Account closed |
| `TransferInitiated` | Transfer started by saga |
| `TransferDebited` | Source account debited |
| `TransferCompleted` | Transfer succeeded |
| `TransferFailed` | Transfer failed after compensation |
| `TransferReversed` | Compensation: debit reversed |

### Aggregate: `Account`

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRoot

@dataclass
class Account(AggregateRoot):
    owner_name: str = ""
    balance: Decimal = Decimal("0")
    status: AccountStatus = AccountStatus.ACTIVE   # ACTIVE | SUSPENDED | CLOSED
    transactions: list = field(default_factory=list)
```

Key methods: `open()`, `deposit()`, `withdraw()`, `suspend()`, `reactivate()`, `close()`.
Business rules: no overdraft, no ops on suspended/closed accounts, no closing with non-zero balance.

## Transfer Saga Flow

```
TransferMoney command
  ↓
TransferInitiated → TransferSaga
  ↓
WithdrawMoney (debit source)
  ↓
TransferDebited → TransferSaga
  ↓
DepositMoney (credit destination)
  ↓  success              ↓  failure
TransferCompleted ✅      DepositMoney (re-credit source)
                            ↓
                          TransferReversed → TransferFailed ❌
```

## Code Structure

```
bases/orchestrix/banking_demo/
├── main.py       # Runnable entry point (async demo)
├── models.py     # Commands, Events, Enums
├── aggregate.py  # Account aggregate
├── handlers.py   # BankingCommandHandlers
├── saga.py       # TransferSaga
└── README.md
```

## Usage Example

```python
import asyncio
from decimal import Decimal
from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore

from bases.orchestrix.banking_demo.aggregate import Account
from bases.orchestrix.banking_demo.models import OpenAccount, DepositMoney

async def main():
    store = InMemoryEventStore()
    repo = AggregateRepository(event_store=store)

    # Open account
    agg = Account()
    agg.open(OpenAccount(account_id="acc-1", owner_name="Alice", initial_balance=Decimal("1000")))
    repo.save(agg)

    # Deposit
    agg = repo.load(Account, "acc-1")
    agg.deposit(DepositMoney(account_id="acc-1", amount=Decimal("500"), description="Bonus"))
    repo.save(agg)

    print(f"Balance: {agg.balance}")  # 1500

asyncio.run(main())
```

## Related

- [E-Commerce Demo](ecommerce.md) — Multi-aggregate saga for order processing
- [Notifications Demo](notifications.md) — Retry logic and error handling
- [Event Store Guide](../guide/event-store.md) — Persistence deep-dive
