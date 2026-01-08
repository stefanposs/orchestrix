# Banking: Money Transfers with Compensation

This example demonstrates money transfers between accounts with automatic compensation when transfers fail, showcasing the Saga pattern and event sourcing.

> **📂 Source Code:**  
> Complete Example: [`bases/orchestrix/banking/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/banking)  
> Main Demo: [`bases/orchestrix/banking/main.py`](https://github.com/stefanposs/orchestrix/blob/main/bases/orchestrix/banking/main.py)  
> Domain Models: [`bases/orchestrix/banking/models.py`](https://github.com/stefanposs/orchestrix/blob/main/bases/orchestrix/banking/models.py)

## Overview

The banking example demonstrates:

- ✅ **Money Transfers** - Between accounts with saga coordination
- ✅ **Automatic Compensation** - Rollback on failure
- ✅ **Event-Sourced Balances** - Balance calculated from events
- ✅ **Two-Phase Commit** - Distributed transaction pattern
- ✅ **Transaction Audit Trail** - Complete immutable history

## Quick Start

```bash
# Run the banking demo
uv run python bases/orchestrix/banking/main.py
```

## Architecture

The transfer saga coordinates a distributed transaction:

```
TransferMoney Command
    ↓
TransferInitiated Event → TransferSaga
    ↓
WithdrawMoney Command (Debit source)
    ↓
TransferDebited Event → TransferSaga
    ↓
DepositMoney Command (Credit destination)
    ↓
TransferCompleted Event ✅
```

### Compensation Flow

If the destination deposit fails, the saga automatically compensates:

```
DepositMoney fails (e.g., account closed)
    ↓
DepositMoney Command (Re-credit source)
    ↓
TransferReversed Event
    ↓
TransferFailed Event ❌
```

## Domain Model

### Commands

#### OpenAccount
```python
@dataclass(frozen=True, kw_only=True)
class OpenAccount(Command):
    account_id: str
    owner_name: str
    initial_balance: Decimal
```

#### TransferMoney
```python
@dataclass(frozen=True, kw_only=True)
class TransferMoney(Command):
    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: str
```

#### WithdrawMoney / DepositMoney
```python
@dataclass(frozen=True, kw_only=True)
class WithdrawMoney(Command):
    account_id: str
    amount: Decimal
    transaction_id: str
    description: str

@dataclass(frozen=True, kw_only=True)
class DepositMoney(Command):
    account_id: str
    amount: Decimal
    transaction_id: str
    description: str
```

### Events

- `AccountOpened` - Account created with initial balance
- `MoneyDeposited` - Funds added to account
- `MoneyWithdrawn` - Funds removed from account
- `TransferInitiated` - Transfer started by saga
- `TransferDebited` - Source account debited
- `TransferCompleted` - Transfer successful
- `TransferReversed` - Compensation executed
- `TransferFailed` - Transfer failed after compensation

### Aggregate

#### Account
```python
@dataclass
class Account:
    account_id: str
    owner_name: str
    balance: Decimal
    status: AccountStatus  # ACTIVE, SUSPENDED, CLOSED
    
    def withdraw(self, amount: Decimal, txn_id: str, description: str):
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        # Emit MoneyWithdrawn event
    
    def deposit(self, amount: Decimal, txn_id: str, description: str):
        # Emit MoneyDeposited event
```

## Key Patterns

### 1. Two-Phase Commit

The transfer saga implements a distributed transaction:

1. **Phase 1**: Debit source account
   ```python
   await bus.send(WithdrawMoney(
       account_id=from_account,
       amount=amount,
       ...
   ))
   ```

2. **Phase 2**: Credit destination account
   ```python
   await bus.send(DepositMoney(
       account_id=to_account,
       amount=amount,
       ...
   ))
   ```

3. **Compensation**: If phase 2 fails, reverse phase 1
   ```python
   await bus.send(DepositMoney(
       account_id=from_account,  # Refund
       amount=amount,
       ...
   ))
   ```

### 2. Event-Sourced Balance

Account balance is calculated from events, not stored directly:

```python
balance = Decimal("0")
for event in events:
    if isinstance(event, AccountOpened):
        balance = event.initial_balance
    elif isinstance(event, MoneyDeposited):
        balance += event.amount
    elif isinstance(event, MoneyWithdrawn):
        balance -= event.amount
```

**Benefits:**
- Complete audit trail
- Temporal queries ("balance at time X")
- Replay for debugging
- No lost updates

### 3. Saga State Management

The saga stores state implicitly through events:

```python
class TransferSaga:
    def on_transfer_initiated(self, event: TransferInitiated):
        # Start phase 1: debit source
        self.send(WithdrawMoney(...))
    
    def on_transfer_debited(self, event: TransferDebited):
        # Phase 1 complete, start phase 2: credit destination
        self.send(DepositMoney(...))
    
    def on_money_deposited(self, event: MoneyDeposited):
        # Phase 2 complete, transfer successful
        self.send(CompleteTransfer(...))
```

### 4. Transaction Log

All balance changes are immutable events providing a complete transaction history:

```python
# Load transaction history
events = await event_store.load_async("account-123")

for event in events:
    if isinstance(event, MoneyWithdrawn):
        print(f"Debit:  ${event.amount} - {event.description}")
    elif isinstance(event, MoneyDeposited):
        print(f"Credit: ${event.amount} - {event.description}")
```

## Business Rules

### Account Rules

- ✅ Initial balance cannot be negative
- ✅ Cannot withdraw more than balance (no overdraft)
- ✅ Cannot operate on suspended/closed accounts
- ✅ Cannot close account with non-zero balance

### Transfer Rules

- ✅ Both accounts must be active
- ✅ Source must have sufficient funds
- ✅ If destination fails, source is automatically refunded
- ✅ Transfer ID must be unique (idempotency)

## Usage Example

```python
import asyncio
from decimal import Decimal

from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus

from examples.banking.aggregate import Account
from examples.banking.handlers import register_handlers
from examples.banking.models import OpenAccount, TransferMoney
from examples.banking.saga import register_saga


async def main():
    # Setup infrastructure
    event_store = InMemoryEventStore()
    message_bus = InMemoryMessageBus()
    repository = AggregateRepository(event_store)

    # Register handlers and saga
    register_handlers(message_bus, repository)
    register_saga(message_bus, repository)

    # Open two accounts
    await message_bus.publish_async(
        OpenAccount(
            account_id="acc-alice",
            owner_name="Alice",
            initial_balance=Decimal("1000.00"),
        )
    )
    await message_bus.publish_async(
        OpenAccount(
            account_id="acc-bob",
            owner_name="Bob",
            initial_balance=Decimal("500.00"),
        )
    )

    # Transfer money from Alice to Bob
    await message_bus.publish_async(
        TransferMoney(
            transfer_id="txn-001",
            from_account_id="acc-alice",
            to_account_id="acc-bob",
            amount=Decimal("250.00"),
            description="Payment for services",
        )
    )

    # Wait for saga to complete
    await asyncio.sleep(0.1)

    # Check final balances
    alice = await repository.load_async(Account, "acc-alice")
    bob = await repository.load_async(Account, "acc-bob")

    print(f"Alice balance: ${alice.balance}")  # $750.00
    print(f"Bob balance: ${bob.balance}")      # $750.00


if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

### Test Insufficient Funds

```python
async def test_insufficient_funds():
    # Setup
    account = Account()
    account.open("test-1", "Test User", Decimal("100.00"))

    # Try to withdraw more than balance
    with pytest.raises(ValueError, match="Insufficient balance"):
        account.withdraw(Decimal("200.00"), "txn-1", "Test withdrawal")
```

### Test Transfer Compensation

```python
async def test_transfer_compensation():
    # Setup: Alice has money, Bob's account is closed
    alice = Account()
    alice.open("alice", "Alice", Decimal("1000.00"))
    await repository.save_async(alice)

    bob = Account()
    bob.open("bob", "Bob", Decimal("0.00"))
    bob.close()  # Close Bob's account
    await repository.save_async(bob)

    # Try to transfer (will fail and compensate)
    await message_bus.publish_async(
        TransferMoney(
            transfer_id="txn-1",
            from_account_id="alice",
            to_account_id="bob",
            amount=Decimal("100.00"),
            description="Test transfer",
        )
    )

    # Wait for compensation
    await asyncio.sleep(0.1)

    # Verify Alice's money was returned
    alice_final = await repository.load_async(Account, "alice")
    assert alice_final.balance == Decimal("1000.00")
```

## Projections

Build account statement projection from events:

```python
@dataclass
class AccountStatement:
    account_id: str
    transactions: list[dict]

    @classmethod
    async def build(cls, account_id: str, event_store):
        events = await event_store.load_async(account_id)
        transactions = []

        for event in events:
            if event.type == "MoneyDeposited":
                transactions.append({
                    "type": "Credit",
                    "amount": event.data.amount,
                    "description": event.data.description,
                    "timestamp": event.data.deposited_at,
                    "balance_after": calculate_balance_after(event),
                })
            elif event.type == "MoneyWithdrawn":
                transactions.append({
                    "type": "Debit",
                    "amount": event.data.amount,
                    "description": event.data.description,
                    "timestamp": event.data.withdrawn_at,
                    "balance_after": calculate_balance_after(event),
                })

        return cls(account_id=account_id, transactions=transactions)

# Usage
statement = await AccountStatement.build("acc-alice", event_store)
for txn in statement.transactions:
    print(f"{txn['type']}: ${txn['amount']} - {txn['description']}")
```

## Production Considerations

### 1. Idempotency

Track transfer IDs to prevent duplicate processing:

```python
processed_transfers = set()

async def handle_transfer(command: TransferMoney):
    if command.transfer_id in processed_transfers:
        return  # Already processed
    
    # Process transfer
    await saga.initiate_transfer(command)
    
    processed_transfers.add(command.transfer_id)
```

### 2. Timeout Handling

Add saga timeout for stuck transfers:

```python
class TransferSaga:
    timeout: timedelta = timedelta(minutes=5)
    
    async def check_timeouts(self):
        for transfer_id, initiated_at in self.pending_transfers.items():
            if datetime.now() - initiated_at > self.timeout:
                await self.cancel_transfer(transfer_id, "Timeout")
```

### 3. Retry Logic

Retry failed operations with exponential backoff:

```python
@retry(
    max_attempts=3,
    backoff=exponential_backoff(initial=1.0, multiplier=2.0),
    exceptions=(NetworkError, TimeoutError)
)
async def send_deposit_command(command: DepositMoney):
    await message_bus.send(command)
```

### 4. Concurrency Control

Use optimistic locking to prevent race conditions:

```python
class Account:
    version: int = 0
    
    async def save(self):
        expected_version = self.version
        # Save will fail if version doesn't match
        await repository.save(self, expected_version=expected_version)
```

### 5. Monitoring

Track transfer metrics:

```python
metrics = {
    "transfers_initiated": Counter(),
    "transfers_completed": Counter(),
    "transfers_failed": Counter(),
    "compensation_executed": Counter(),
    "avg_transfer_duration": Histogram(),
}

# Usage
metrics["transfers_initiated"].inc()
start = time.time()
# ... process transfer ...
metrics["avg_transfer_duration"].observe(time.time() - start)
```

## Related Examples

- **[E-Commerce](ecommerce.md)** - Multi-aggregate sagas for order processing
- **[Notifications](notifications.md)** - Retry logic and error handling
- **[Lakehouse Platform](lakehouse.md)** - Event sourcing with compliance

## Learn More

- [Saga Pattern Guide](../guide/best-practices.md#sagas)
- [Event Sourcing](../guide/event-store.md)
- [Testing Strategies](../development/testing.md)

## Source Code

- [`aggregate.py`](https://github.com/stefanposs/orchestrix/blob/main/bases/orchestrix/banking/aggregate.py) - Account aggregate
- [`saga.py`](https://github.com/stefanposs/orchestrix/blob/main/bases/orchestrix/banking/saga.py) - Transfer saga coordinator
- [`handlers.py`](https://github.com/stefanposs/orchestrix/blob/main/bases/orchestrix/banking/handlers.py) - Command handlers
- [`models.py`](https://github.com/stefanposs/orchestrix/blob/main/bases/orchestrix/banking/models.py) - Commands and events

[**Browse Complete Example →**](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/banking)
