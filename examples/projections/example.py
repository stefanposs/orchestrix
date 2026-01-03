"""CQRS Projection Example: Building a Read Model.

This example demonstrates how to use the ProjectionEngine to build
read models from an event stream. We build an OrderSummary read model
that tracks the state of orders for fast queries.

Key concepts:
- Projections consume events to build read models
- Read models are optimized for queries (not mutation)
- Projections provide eventual consistency
- State tracking enables exactly-once semantics
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from orchestrix.core import Event, ProjectionEngine, InMemoryProjectionStateStore


# Domain events
@dataclass(frozen=True)
class OrderCreated(Event):
    """Event: order was created."""

    order_id: str
    customer_id: str
    customer_name: str
    amount: float


@dataclass(frozen=True)
class ItemAddedToOrder(Event):
    """Event: item was added to order."""

    order_id: str
    item_id: str
    item_name: str
    quantity: int
    unit_price: float


@dataclass(frozen=True)
class OrderConfirmed(Event):
    """Event: order was confirmed by customer."""

    order_id: str


@dataclass(frozen=True)
class OrderShipped(Event):
    """Event: order was shipped."""

    order_id: str
    carrier: str
    tracking_number: str


@dataclass(frozen=True)
class OrderDelivered(Event):
    """Event: order was delivered."""

    order_id: str


@dataclass(frozen=True)
class OrderCancelled(Event):
    """Event: order was cancelled."""

    order_id: str
    reason: str


# Read model: OrderSummary
@dataclass
class OrderItem:
    """Item in an order."""

    item_id: str
    item_name: str
    quantity: int
    unit_price: float

    @property
    def total_price(self) -> float:
        """Calculate total price for this item."""
        return self.quantity * self.unit_price


@dataclass
class OrderSummary:
    """Read model: summary of an order."""

    order_id: str
    customer_id: str
    customer_name: str
    status: str = "draft"  # draft, confirmed, shipped, delivered, cancelled
    items: list[OrderItem] = field(default_factory=list)
    total_amount: float = 0.0
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    cancellation_reason: Optional[str] = None

    def add_item(self, item: OrderItem) -> None:
        """Add an item to the order."""
        self.items.append(item)
        self.total_amount += item.total_price

    def confirm(self) -> None:
        """Confirm the order."""
        self.status = "confirmed"

    def ship(self, carrier: str, tracking_number: str) -> None:
        """Mark order as shipped."""
        self.status = "shipped"
        self.carrier = carrier
        self.tracking_number = tracking_number

    def deliver(self) -> None:
        """Mark order as delivered."""
        self.status = "delivered"

    def cancel(self, reason: str) -> None:
        """Cancel the order."""
        self.status = "cancelled"
        self.cancellation_reason = reason


class OrderReadModelProjection:
    """Projection that builds the OrderSummary read model."""

    def __init__(self):
        """Initialize the projection."""
        # In-memory read model storage (would be a database in production)
        self.read_models: dict[str, OrderSummary] = {}

    async def initialize(self) -> None:
        """Initialize the projection engine.

        In production, would load existing state and event stream.
        """
        self.engine = ProjectionEngine(
            projection_id="order-summary",
            state_store=InMemoryProjectionStateStore(),
        )
        await self.engine.initialize()

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register handlers for all event types."""

        @self.engine.on(OrderCreated)
        async def on_order_created(event: OrderCreated) -> None:
            summary = OrderSummary(
                order_id=event.order_id,
                customer_id=event.customer_id,
                customer_name=event.customer_name,
                total_amount=event.amount,
            )
            self.read_models[event.order_id] = summary
            print(
                f"✓ Order created: {event.order_id} for {event.customer_name}"
            )

        @self.engine.on(ItemAddedToOrder)
        async def on_item_added(event: ItemAddedToOrder) -> None:
            if order := self.read_models.get(event.order_id):
                item = OrderItem(
                    item_id=event.item_id,
                    item_name=event.item_name,
                    quantity=event.quantity,
                    unit_price=event.unit_price,
                )
                order.add_item(item)
                print(
                    f"  ✓ Item added: {event.item_name} "
                    f"(x{event.quantity} @ ${event.unit_price})"
                )

        @self.engine.on(OrderConfirmed)
        async def on_order_confirmed(event: OrderConfirmed) -> None:
            if order := self.read_models.get(event.order_id):
                order.confirm()
                print(f"✓ Order confirmed")

        @self.engine.on(OrderShipped)
        async def on_order_shipped(event: OrderShipped) -> None:
            if order := self.read_models.get(event.order_id):
                order.ship(event.carrier, event.tracking_number)
                print(
                    f"✓ Order shipped via {event.carrier} "
                    f"({event.tracking_number})"
                )

        @self.engine.on(OrderDelivered)
        async def on_order_delivered(event: OrderDelivered) -> None:
            if order := self.read_models.get(event.order_id):
                order.deliver()
                print(f"✓ Order delivered")

        @self.engine.on(OrderCancelled)
        async def on_order_cancelled(event: OrderCancelled) -> None:
            if order := self.read_models.get(event.order_id):
                order.cancel(event.reason)
                print(f"✓ Order cancelled: {event.reason}")

    async def process_events(self, events: list[Event]) -> None:
        """Process a stream of events.

        Args:
            events: List of domain events
        """
        await self.engine.process_events(events)

    def get_order_summary(self, order_id: str) -> Optional[OrderSummary]:
        """Query the read model.

        Args:
            order_id: The order to look up

        Returns:
            The order summary or None if not found
        """
        return self.read_models.get(order_id)

    def list_orders_by_status(self, status: str) -> list[OrderSummary]:
        """Query orders by status.

        Args:
            status: The status to filter by

        Returns:
            List of orders with that status
        """
        return [order for order in self.read_models.values() if order.status == status]

    def print_summary(self, order_id: str) -> None:
        """Print a formatted order summary.

        Args:
            order_id: The order to display
        """
        if order := self.get_order_summary(order_id):
            print(f"\n{'='*60}")
            print(f"Order Summary: {order_id}")
            print(f"{'='*60}")
            print(f"Customer: {order.customer_name} ({order.customer_id})")
            print(f"Status: {order.status.upper()}")
            print(f"\nItems:")
            for item in order.items:
                print(
                    f"  {item.item_name} x{item.quantity} "
                    f"@ ${item.unit_price} = ${item.total_price:.2f}"
                )
            print(f"\nTotal: ${order.total_amount:.2f}")
            if order.carrier:
                print(
                    f"Shipping: {order.carrier} (Tracking: {order.tracking_number})"
                )
            if order.cancellation_reason:
                print(f"Cancellation Reason: {order.cancellation_reason}")
            print(f"{'='*60}\n")


async def main() -> None:
    """Run the projection example."""
    print("\n" + "=" * 60)
    print("CQRS Projection Example: Order Read Models")
    print("=" * 60 + "\n")

    # Create and initialize the projection
    projection = OrderReadModelProjection()
    await projection.initialize()

    # Simulate a stream of events
    print("Processing events...\n")

    events = [
        # Order 1: Complete happy path
        OrderCreated(
            order_id="ORDER-001",
            customer_id="CUST-001",
            customer_name="Alice Johnson",
            amount=149.99,
        ),
        ItemAddedToOrder(
            order_id="ORDER-001",
            item_id="SKU-001",
            item_name="Wireless Keyboard",
            quantity=1,
            unit_price=79.99,
        ),
        ItemAddedToOrder(
            order_id="ORDER-001",
            item_id="SKU-002",
            item_name="Mouse",
            quantity=1,
            unit_price=39.99,
        ),
        OrderConfirmed(order_id="ORDER-001"),
        OrderShipped(
            order_id="ORDER-001", carrier="FedEx", tracking_number="1234567890"
        ),
        OrderDelivered(order_id="ORDER-001"),
        # Order 2: Cancelled
        OrderCreated(
            order_id="ORDER-002",
            customer_id="CUST-002",
            customer_name="Bob Smith",
            amount=99.99,
        ),
        ItemAddedToOrder(
            order_id="ORDER-002",
            item_id="SKU-003",
            item_name="USB Hub",
            quantity=2,
            unit_price=29.99,
        ),
        OrderConfirmed(order_id="ORDER-002"),
        OrderCancelled(order_id="ORDER-002", reason="Customer requested cancellation"),
    ]

    # Process all events through the projection
    await projection.process_events(events)

    # Query the read model
    print("\n" + "=" * 60)
    print("Querying Read Models")
    print("=" * 60 + "\n")

    projection.print_summary("ORDER-001")
    projection.print_summary("ORDER-002")

    # Show orders by status
    print("Orders by status:")
    for status in ["delivered", "confirmed", "cancelled"]:
        orders = projection.list_orders_by_status(status)
        print(f"\n{status.upper()}: {len(orders)} order(s)")
        for order in orders:
            print(f"  - {order.order_id}: {order.customer_name} (${order.total_amount:.2f})")

    # Show projection health
    print(f"\n{'='*60}")
    print("Projection Health")
    print(f"{'='*60}")
    print(f"Healthy: {projection.engine.is_healthy()}")
    state = projection.engine.get_state()
    if state:
        print(f"Last event processed: {state.last_processed_event_id}")
        print(f"Total errors: {state.error_count}")
        print(f"Last updated: {state.updated_at}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
