#!/usr/bin/env python3
"""
Simple example demonstrating Orchestrix usage.

Run this script to see the OrderModule in action:
    python examples/run_order_example.py
"""

from order_module import CancelOrder, CreateOrder, OrderModule

from orchestrix.infrastructure import InMemoryEventStore, InMemoryMessageBus


def main():
    """Run the order example."""
    print("=" * 60)
    print("🚀 Orchestrix Order Module Example")
    print("=" * 60)
    print()

    # 1. Setup infrastructure
    bus = InMemoryMessageBus()
    store = InMemoryEventStore()

    # 2. Register module
    module = OrderModule()
    module.register(bus, store)

    print("✅ Infrastructure initialized")
    print("✅ OrderModule registered")
    print()
    print("-" * 60)
    print()

    # 3. Execute commands
    # Create an order
    create_cmd = CreateOrder(order_id="ORD-001", customer_name="Alice Johnson", total_amount=149.99)
    bus.publish(create_cmd)

    # Create another order
    create_cmd2 = CreateOrder(order_id="ORD-002", customer_name="Bob Smith", total_amount=299.50)
    bus.publish(create_cmd2)

    # Cancel the first order
    cancel_cmd = CancelOrder(order_id="ORD-001", reason="Customer requested refund")
    bus.publish(cancel_cmd)

    print("-" * 60)
    print()
    print("📊 Event Store Contents:")
    print()

    # 4. Inspect event store
    for order_id in ["ORD-001", "ORD-002"]:
        events = store.load(order_id)
        print(f"  {order_id}: {len(events)} event(s)")
        for event in events:
            print(f"    - {event.type}")

    print()
    print("=" * 60)
    print("✨ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
