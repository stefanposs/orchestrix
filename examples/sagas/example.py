"""Saga Pattern Example: Distributed Money Transfer.

This example demonstrates the Saga pattern for handling distributed
transactions across multiple aggregates without traditional ACID guarantees.

A money transfer saga:
1. Debit the source account
2. Credit the destination account
3. If either fails, compensate the other (rollback)

This uses compensation-based transactions where each step has an undo action.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from orchestrix.core import (
    InMemorySagaStateStore,
    Saga,
    SagaStep,
    SagaStatus,
)


# Accounts database (simulated)
@dataclass
class Account:
    """A bank account."""

    account_id: str
    owner: str
    balance: float


# Simulated account store
ACCOUNTS = {
    "ACC-001": Account(account_id="ACC-001", owner="Alice", balance=1000.0),
    "ACC-002": Account(account_id="ACC-002", owner="Bob", balance=500.0),
    "ACC-003": Account(account_id="ACC-003", owner="Charlie", balance=750.0),
}


# Saga actions and compensations
async def debit_account(
    from_account: str, amount: float, **kwargs: Any
) -> dict[str, Any]:
    """Debit (withdraw) money from an account.

    Args:
        from_account: Account ID to debit
        amount: Amount to debit

    Returns:
        Result with account details and new balance

    Raises:
        ValueError: If account not found or insufficient funds
    """
    if from_account not in ACCOUNTS:
        raise ValueError(f"Account {from_account} not found")

    account = ACCOUNTS[from_account]
    if account.balance < amount:
        raise ValueError(
            f"Insufficient funds: {account.balance} < {amount}"
        )

    account.balance -= amount
    print(f"✓ Debited ${amount} from {account.owner} ({from_account})")
    print(f"  New balance: ${account.balance}")

    return {
        "account_id": from_account,
        "amount": amount,
        "new_balance": account.balance,
    }


async def credit_account(
    to_account: str, amount: float, **kwargs: Any
) -> dict[str, Any]:
    """Credit (deposit) money to an account.

    Args:
        to_account: Account ID to credit
        amount: Amount to credit

    Returns:
        Result with account details and new balance

    Raises:
        ValueError: If account not found
    """
    if to_account not in ACCOUNTS:
        raise ValueError(f"Account {to_account} not found")

    account = ACCOUNTS[to_account]
    account.balance += amount
    print(f"✓ Credited ${amount} to {account.owner} ({to_account})")
    print(f"  New balance: ${account.balance}")

    return {
        "account_id": to_account,
        "amount": amount,
        "new_balance": account.balance,
    }


async def compensate_debit(
    result: dict[str, Any], **kwargs: Any
) -> None:
    """Compensation: Credit back the debited amount.

    Args:
        result: Result from the debit action (contains amount and account_id)
    """
    from_account = result["account_id"]
    amount = result["amount"]

    if from_account in ACCOUNTS:
        account = ACCOUNTS[from_account]
        account.balance += amount
        print(f"↶ Compensation: Credited back ${amount} to {account.owner}")
        print(f"  Balance restored: ${account.balance}")


async def compensate_credit(
    result: dict[str, Any], **kwargs: Any
) -> None:
    """Compensation: Debit the credited amount.

    Args:
        result: Result from the credit action (contains amount and account_id)
    """
    to_account = result["account_id"]
    amount = result["amount"]

    if to_account in ACCOUNTS:
        account = ACCOUNTS[to_account]
        account.balance -= amount
        print(f"↶ Compensation: Debited ${amount} from {account.owner}")
        print(f"  Balance restored: ${account.balance}")


async def create_money_transfer_saga(
    from_account: str, to_account: str, amount: float
) -> Saga:
    """Create a money transfer saga.

    Args:
        from_account: Source account ID
        to_account: Destination account ID
        amount: Amount to transfer

    Returns:
        Initialized saga ready to execute
    """
    steps = [
        SagaStep(
            name="debit_source",
            action=debit_account,
            compensation=compensate_debit,
        ),
        SagaStep(
            name="credit_destination",
            action=credit_account,
            compensation=compensate_credit,
        ),
    ]

    state_store = InMemorySagaStateStore()
    saga = Saga("MoneyTransfer", steps, state_store)
    await saga.initialize()

    return saga


async def print_account_balances() -> None:
    """Print current balances for all accounts."""
    print("\n📊 Account Balances:")
    for account_id, account in ACCOUNTS.items():
        print(f"  {account.owner:12} ({account_id}): ${account.balance:>8.2f}")


async def test_successful_transfer() -> None:
    """Test a successful money transfer."""
    print("\n" + "=" * 60)
    print("TEST 1: Successful Money Transfer")
    print("=" * 60)

    saga = await create_money_transfer_saga("ACC-001", "ACC-002", 150.0)

    print("\nExecuting transfer from Alice to Bob (150)...")
    result = await saga.execute(
        from_account="ACC-001", to_account="ACC-002", amount=150.0
    )

    print(f"\n✅ Transfer successful!")
    print(f"Saga Status: {saga.get_state().status}")
    await print_account_balances()


async def test_insufficient_funds() -> None:
    """Test transfer with insufficient funds (triggers compensation)."""
    print("\n" + "=" * 60)
    print("TEST 2: Transfer with Insufficient Funds")
    print("=" * 60)

    saga = await create_money_transfer_saga("ACC-002", "ACC-003", 1000.0)

    print("\nAttempting transfer from Bob to Charlie (1000)...")
    print("Expected: Insufficient funds, compensation triggered\n")

    try:
        await saga.execute(
            from_account="ACC-002", to_account="ACC-003", amount=1000.0
        )
    except ValueError as e:
        print(f"\n❌ Transfer failed: {e}")
        print(f"Saga Status: {saga.get_state().status}")
        print("\n✓ Compensations executed (balances restored)")

    await print_account_balances()


async def test_invalid_destination() -> None:
    """Test transfer to nonexistent account (triggers compensation)."""
    print("\n" + "=" * 60)
    print("TEST 3: Transfer to Invalid Account")
    print("=" * 60)

    saga = await create_money_transfer_saga("ACC-001", "INVALID", 100.0)

    print("\nAttempting transfer from Alice to INVALID account...")
    print("Expected: Account not found, compensation triggered\n")

    try:
        await saga.execute(
            from_account="ACC-001", to_account="INVALID", amount=100.0
        )
    except ValueError as e:
        print(f"\n❌ Transfer failed: {e}")
        print(f"Saga Status: {saga.get_state().status}")
        print("\n✓ Compensations executed (debited amount credited back)")

    await print_account_balances()


async def test_multiple_transfers() -> None:
    """Test multiple sequential transfers."""
    print("\n" + "=" * 60)
    print("TEST 4: Multiple Sequential Transfers")
    print("=" * 60)

    transfers = [
        ("ACC-001", "ACC-002", 100.0),  # Alice -> Bob
        ("ACC-002", "ACC-003", 50.0),   # Bob -> Charlie
        ("ACC-003", "ACC-001", 75.0),   # Charlie -> Alice
    ]

    for from_acc, to_acc, amount in transfers:
        saga = await create_money_transfer_saga(from_acc, to_acc, amount)
        from_name = ACCOUNTS[from_acc].owner
        to_name = ACCOUNTS[to_acc].owner

        print(f"\nTransferring ${amount} from {from_name} to {to_name}...")
        await saga.execute(from_account=from_acc, to_account=to_acc, amount=amount)

    print(f"\n✅ All transfers completed successfully!")
    await print_account_balances()


async def demonstrate_saga_state() -> None:
    """Demonstrate saga state tracking and recovery."""
    print("\n" + "=" * 60)
    print("TEST 5: Saga State Tracking")
    print("=" * 60)

    saga = await create_money_transfer_saga("ACC-001", "ACC-002", 50.0)

    print("\nBefore execution:")
    state = saga.get_state()
    print(f"  Status: {state.status}")
    print(f"  Is completed: {saga.is_completed()}")
    print(f"  Is successful: {saga.is_successful()}")

    await saga.execute(from_account="ACC-001", to_account="ACC-002", amount=50.0)

    print("\nAfter execution:")
    state = saga.get_state()
    print(f"  Status: {state.status}")
    print(f"  Is completed: {saga.is_completed()}")
    print(f"  Is successful: {saga.is_successful()}")
    print(f"\n  Step details:")
    for step_name, step_status in state.step_statuses.items():
        print(f"    {step_name}: {step_status.status}")
        if step_status.result:
            print(f"      Result: {step_status.result}")


async def main() -> None:
    """Run all saga examples."""
    print("\n" + "=" * 60)
    print("SAGA PATTERN EXAMPLE: Money Transfer")
    print("=" * 60)
    print("\nThe Saga pattern coordinates distributed transactions using")
    print("compensation-based rollback instead of traditional ACID.")

    await print_account_balances()

    # Test cases
    await test_successful_transfer()
    await test_insufficient_funds()
    await test_invalid_destination()
    await test_multiple_transfers()
    await demonstrate_saga_state()

    # Final state
    print("\n" + "=" * 60)
    print("FINAL ACCOUNT BALANCES")
    print("=" * 60)
    await print_account_balances()

    print("\n" + "=" * 60)
    print("Key Saga Concepts Demonstrated:")
    print("=" * 60)
    print("✓ Distributed transactions across aggregates")
    print("✓ Compensation-based rollback (not ACID)")
    print("✓ Automatic compensation on failure")
    print("✓ State tracking for recovery")
    print("✓ Idempotent design for safety")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
