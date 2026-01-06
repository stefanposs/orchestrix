# Banking Demo

This example demonstrates money transfers between accounts with automatic
compensation when transfers fail.

## Architecture

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
TransferCompleted Event
```

## Compensation Flow

If destination deposit fails:
```
DepositMoney fails (e.g., account closed)
    ↓
DepositMoney Command (Re-credit source - compensation)
    ↓
TransferReversed Event
    ↓
TransferFailed Event
```

## Usage

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
    # Setup
    event_store = InMemoryEventStore()
    message_bus = InMemoryMessageBus()
    repository = AggregateRepository(event_store)

    register_handlers(message_bus, repository)
    register_saga(message_bus, repository)

    # Open two accounts
    await message_bus.publish_async(
        OpenAccount(
            account_id="acc-1",
            owner_name="Alice",
            initial_balance=Decimal("1000.00"),
        )
    )
    await message_bus.publish_async(
        OpenAccount(
            account_id="acc-2",
            owner_name="Bob",
            initial_balance=Decimal("500.00"),
        )
    )

    # Transfer money
    await message_bus.publish_async(
        TransferMoney(
            transfer_id="txn-1",
            from_account_id="acc-1",
            to_account_id="acc-2",
            amount=Decimal("250.00"),
            description="Payment for services",
        )
    )

    # Check balances
    alice = await repository.load_async(Account, "acc-1")
    bob = await repository.load_async(Account, "acc-2")
    print(f"Alice balance: ${alice.balance}")  # $750.00
    print(f"Bob balance: ${bob.balance}")      # $750.00


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Patterns

### 1. Two-Phase Commit
Transfer saga implements distributed transaction:
1. **Phase 1**: Debit source account
2. **Phase 2**: Credit destination account
3. **Compensation**: If phase 2 fails, reverse phase 1

### 2. Event-Sourced Balance
Account balance is calculated from events:
- AccountOpened → Set initial balance
- MoneyDeposited → Increase balance
- MoneyWithdrawn → Decrease balance

### 3. Transaction Log
All balance changes are immutable events:
```python
# Load transaction history
events = await event_store.load_async("acc-1")
for event in events:
    print(f"{event.type}: {event.data}")
```

### 4. Saga State Management
Saga stores state implicitly in events:
- TransferInitiated → Transfer exists
- TransferDebited → Source debited, destination pending
- TransferCompleted → Both accounts updated
- TransferReversed → Compensation executed

## Business Rules

**Account Rules:**
- Initial balance cannot be negative
- Cannot withdraw more than balance (no overdraft)
- Cannot operate on suspended/closed accounts
- Cannot close account with non-zero balance

**Transfer Rules:**
- Both accounts must be active
- Source must have sufficient funds
- If destination fails, source is automatically refunded

## Testing

```python
async def test_insufficient_funds():
    # Setup
    account = Account()
    account.open("test-1", "Test", Decimal("100.00"))

    # Try to withdraw too much
    with pytest.raises(ValueError, match="Insufficient balance"):
        account.withdraw(Decimal("200.00"), "txn-1", "Test")


async def test_transfer_compensation():
    # Setup accounts
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
            description="Test",
        )
    )

    # Verify Alice's money was returned
    alice_final = await repository.load_async(Account, "alice")
    assert alice_final.balance == Decimal("1000.00")
```

## Projections

Build account statement projection:

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
                })
            elif event.type == "MoneyWithdrawn":
                transactions.append({
                    "type": "Debit",
                    "amount": event.data.amount,
                    "description": event.data.description,
                    "timestamp": event.data.withdrawn_at,
                })

        return cls(account_id=account_id, transactions=transactions)
```

## Production Considerations

1. **Idempotency**: Track transfer IDs to prevent duplicate processing
2. **Timeout Handling**: Add saga timeout for stuck transfers
3. **Retry Logic**: Retry failed deposits with exponential backoff
4. **Audit Trail**: All events are immutable audit log
5. **Concurrency**: Use optimistic locking (version) to prevent race conditions
6. **Monitoring**: Track transfer success/failure rates
7. **Compliance**: Event store provides complete transaction history for audits
"""
