"""Complete e-commerce order processing example."""

import asyncio
from decimal import Decimal

from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.utils import InMemoryEventStore, InMemoryMessageBus

from .aggregate import Order
from .handlers import register_handlers
from .models import Address, CreateOrder, OrderItem
from .saga import register_saga


async def run_example() -> None:
    """Run the e-commerce order processing example."""
    print("🛒 E-Commerce Order Processing Example\n")
    print("=" * 60)

    # Setup infrastructure
    event_store = InMemoryEventStore()
    message_bus = InMemoryMessageBus()
    repository = AggregateRepository[Order](event_store)

    # Register handlers and saga
    handlers = register_handlers(message_bus, repository)
    saga = register_saga(message_bus, repository)

    print("\n✅ Infrastructure initialized")
    print(f"   - Event Store: {type(event_store).__name__}")
    print(f"   - Message Bus: {type(message_bus).__name__}")
    print(f"   - Handlers: {len(handlers.__dict__)} command handlers")
    print(f"   - Saga: {type(saga).__name__}")

    # Create an order
    order_id = "order-123"
    customer_id = "customer-456"

    print(f"\n📦 Creating order {order_id}...")

    command = CreateOrder(
        order_id=order_id,
        customer_id=customer_id,
        items=[
            OrderItem(
                product_id="product-789",
                quantity=2,
                unit_price=Decimal("29.99"),
            ),
            OrderItem(
                product_id="product-101",
                quantity=1,
                unit_price=Decimal("49.99"),
            ),
        ],
        shipping_address=Address(
            street="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA",
        ),
    )

    # Calculate total
    total = sum(item.total_price for item in command.items)
    print(f"   Order Total: ${total}")

    # Publish command (triggers saga)
    await message_bus.publish_async(command)

    # Give saga time to process all steps
    print("\n⏳ Processing order through saga...")
    await asyncio.sleep(0.2)

    # Load order to check final state
    order = await repository.load_async(Order, order_id)

    print("\n" + "=" * 60)
    print("📊 Final Order State:")
    print("=" * 60)
    print(f"Order ID: {order.aggregate_id}")
    print(f"Customer ID: {order.customer_id}")
    print(f"Status: {order.status.value.upper()}")
    print(f"Payment ID: {order.payment_id}")
    print(f"Reservation ID: {order.reservation_id}")
    print(f"Items: {len(order.items)}")

    for i, item in enumerate(order.items, 1):
        print(
            f"  {i}. {item.product_id} x{item.quantity} @ ${item.unit_price} = ${item.total_price}"
        )

    print("\nShipping Address:")
    if order.shipping_address:
        print(f"  {order.shipping_address.street}")
        print(
            f"  {order.shipping_address.city}, {order.shipping_address.state} "
            f"{order.shipping_address.postal_code}"
        )
        print(f"  {order.shipping_address.country}")

    # Show event history
    events = await event_store.load_async(order_id)
    print(f"\n📜 Event History ({len(events)} events):")
    print("=" * 60)

    for i, event in enumerate(events, 1):
        print(f"{i}. {event.type}")
        if hasattr(event, "order_id"):
            print(f"   Order ID: {event.order_id}")
        if hasattr(event, "payment_id"):
            print(f"   Payment ID: {event.payment_id}")
        if hasattr(event, "reservation_id"):
            print(f"   Reservation ID: {event.reservation_id}")

    print("\n✅ Example completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(run_example())
