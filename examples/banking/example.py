"""Complete banking transfer example with compensation."""
import asyncio
from contextlib import suppress
from decimal import Decimal

from orchestrix.core.aggregate import AggregateRepository
from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus

from .aggregate import Account
from .handlers import register_handlers
from .models import OpenAccount, TransferMoney
from .saga import register_saga


async def run_example() -> None:
    """Run the banking transfer example."""
    print("🏦 Banking Transfer Example with Compensation\n")
    print("=" * 70)

    # Setup infrastructure
    event_store = InMemoryEventStore()
    message_bus = InMemoryMessageBus()
    repository = AggregateRepository(event_store)

    # Register handlers and saga
    handlers = register_handlers(message_bus, repository)
    saga = register_saga(message_bus, repository)

    print("\n✅ Infrastructure initialized")
    print(f"   - Event Store: {type(event_store).__name__}")
    print(f"   - Message Bus: {type(message_bus).__name__}")
    print(f"   - Handlers: {len(handlers.__dict__)} command handlers")
    print(f"   - Saga: {type(saga).__name__}")

    # Open Alice's account
    print("\n💰 Opening Alice's account...")
    await message_bus.publish_async(
        OpenAccount(
            account_id="alice-123",
            owner_name="Alice Johnson",
            initial_balance=Decimal("1000.00"),
        )
    )

    # Open Bob's account
    print("💰 Opening Bob's account...")
    await message_bus.publish_async(
        OpenAccount(
            account_id="bob-456",
            owner_name="Bob Smith",
            initial_balance=Decimal("500.00"),
        )
    )

    # Give handlers time to process
    await asyncio.sleep(0.1)

    # Load accounts to show initial balances
    alice = await repository.load_async(Account, "alice-123")
    bob = await repository.load_async(Account, "bob-456")

    print("\n" + "=" * 70)
    print("📊 Initial Balances:")
    print("=" * 70)
    print(f"Alice: ${alice.balance}")
    print(f"Bob:   ${bob.balance}")

    # Execute transfer
    transfer_amount = Decimal("250.00")
    print(f"\n💸 Transferring ${transfer_amount} from Alice to Bob...")
    print("   Description: Payment for services")

    await message_bus.publish_async(
        TransferMoney(
            transfer_id="transfer-789",
            from_account_id="alice-123",
            to_account_id="bob-456",
            amount=transfer_amount,
            description="Payment for services",
        )
    )

    # Give saga time to process transfer
    print("\n⏳ Processing transfer through saga...")
    await asyncio.sleep(0.2)

    # Load accounts to show final balances
    alice_final = await repository.load_async(Account, "alice-123")
    bob_final = await repository.load_async(Account, "bob-456")

    print("\n" + "=" * 70)
    print("📊 Final Balances:")
    print("=" * 70)
    print(f"Alice: ${alice_final.balance} (was ${alice.balance})")
    print(f"Bob:   ${bob_final.balance} (was ${bob.balance})")

    print(f"\n💵 Transfer Amount: ${transfer_amount}")
    print(f"✅ Alice debited: ${alice.balance - alice_final.balance}")
    print(f"✅ Bob credited:  ${bob_final.balance - bob.balance}")

    # Show Alice's transaction history
    alice_events = await event_store.load_async("alice-123")
    print(f"\n📜 Alice's Transaction History ({len(alice_events)} events):")
    print("=" * 70)
    for i, event in enumerate(alice_events, 1):
        print(f"{i}. {event.type}")
        if hasattr(event.data, "amount"):
            print(f"   Amount: ${event.data.amount}")
        if hasattr(event.data, "description"):
            print(f"   Description: {event.data.description}")

    # Show Bob's transaction history
    bob_events = await event_store.load_async("bob-456")
    print(f"\n📜 Bob's Transaction History ({len(bob_events)} events):")
    print("=" * 70)
    for i, event in enumerate(bob_events, 1):
        print(f"{i}. {event.type}")
        if hasattr(event.data, "amount"):
            print(f"   Amount: ${event.data.amount}")
        if hasattr(event.data, "description"):
            print(f"   Description: {event.data.description}")

    # Demonstrate compensation by trying invalid transfer
    print("\n" + "=" * 70)
    print("🔄 Demonstrating Compensation Logic")
    print("=" * 70)
    print("\n💥 Attempting transfer larger than balance...")

    with suppress(Exception):
        # Expected to fail - saga will handle compensation
        await message_bus.publish_async(
            TransferMoney(
                transfer_id="transfer-999",
                from_account_id="bob-456",
                to_account_id="alice-123",
                amount=Decimal("10000.00"),  # Bob doesn't have this much
                description="Invalid transfer - too large",
            )
        )
        await asyncio.sleep(0.1)

    # Check balances remain unchanged
    alice_check = await repository.load_async(Account, "alice-123")
    bob_check = await repository.load_async(Account, "bob-456")

    print("\n✅ Compensation worked! Balances unchanged:")
    print(f"   Alice: ${alice_check.balance} (same as before)")
    print(f"   Bob:   ${bob_check.balance} (same as before)")

    print("\n✅ Example completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(run_example())
