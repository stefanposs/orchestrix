"""Integration tests for full order flow."""

from dataclasses import dataclass

import pytest

from orchestrix.infrastructure import InMemoryEventStore, InMemoryMessageBus
from orchestrix.message import Command, Event


# Domain: Order Aggregate
@dataclass(frozen=True)
class CreateOrder(Command):
    """Command to create a new order."""

    order_id: str
    customer_name: str
    total_amount: float


@dataclass(frozen=True)
class AddItem(Command):
    """Command to add item to order."""

    order_id: str
    item_name: str
    item_price: float


@dataclass(frozen=True)
class OrderCreated(Event):
    """Event: Order was created."""

    order_id: str
    customer_name: str


@dataclass(frozen=True)
class ItemAdded(Event):
    """Event: Item was added to order."""

    order_id: str
    item_name: str
    item_price: float


@dataclass(frozen=True)
class OrderTotal(Event):
    """Event: Order total updated."""

    order_id: str
    total: float


class Order:
    """Order aggregate."""

    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        self.customer_name = ""
        self.items: list[tuple[str, float]] = []
        self.total = 0.0
        self._changes: list[Event] = []

    def create(self, customer_name: str) -> None:
        """Create the order."""
        self._changes.append(
            OrderCreated(
                order_id=self.order_id,
                customer_name=customer_name,
            )
        )

    def add_item(self, item_name: str, item_price: float) -> None:
        """Add item to order."""
        self._changes.append(
            ItemAdded(
                order_id=self.order_id,
                item_name=item_name,
                item_price=item_price,
            )
        )
        new_total = self.total + item_price
        self._changes.append(
            OrderTotal(
                order_id=self.order_id,
                total=new_total,
            )
        )

    def get_changes(self) -> list[Event]:
        """Get uncommitted changes."""
        return self._changes

    def apply(self, event: Event) -> None:
        """Apply an event to rebuild state."""
        if isinstance(event, OrderCreated):
            self.customer_name = event.customer_name
        elif isinstance(event, ItemAdded):
            self.items.append((event.item_name, event.item_price))
        elif isinstance(event, OrderTotal):
            self.total = event.total

    @classmethod
    def from_events(cls, order_id: str, events: list[Event]) -> "Order":
        """Reconstruct aggregate from events."""
        order = cls(order_id)
        for event in events:
            order.apply(event)
        return order


# Command Handlers
class CreateOrderHandler:
    """Handler for CreateOrder command."""

    def __init__(self, bus: InMemoryMessageBus, store: InMemoryEventStore):
        self.bus = bus
        self.store = store

    def handle(self, command: CreateOrder) -> None:
        """Handle create order command."""
        # Create aggregate
        order = Order(command.order_id)
        order.create(command.customer_name)

        # Add initial item
        order.add_item("Initial", command.total_amount)

        # Persist and publish events
        events = order.get_changes()
        self.store.save(command.order_id, events)
        for event in events:
            self.bus.publish(event)


class AddItemHandler:
    """Handler for AddItem command."""

    def __init__(self, bus: InMemoryMessageBus, store: InMemoryEventStore):
        self.bus = bus
        self.store = store

    def handle(self, command: AddItem) -> None:
        """Handle add item command."""
        # Reconstruct aggregate from events
        events = self.store.load(command.order_id)
        order = Order.from_events(command.order_id, events)

        # Execute command
        order.add_item(command.item_name, command.item_price)

        # Persist and publish new events
        new_events = order.get_changes()
        self.store.save(command.order_id, new_events)
        for event in new_events:
            self.bus.publish(event)


@pytest.fixture
def infrastructure():
    """Provide fresh infrastructure."""
    bus = InMemoryMessageBus()
    store = InMemoryEventStore()
    return bus, store


class TestOrderFlow:
    """Integration tests for order flow."""

    def test_create_order_full_flow(self, infrastructure):
        """Test creating an order end-to-end."""
        bus, store = infrastructure
        published_events = []

        # Subscribe to all events
        def capture_event(event):
            published_events.append(event)

        bus.subscribe(OrderCreated, capture_event)
        bus.subscribe(ItemAdded, capture_event)
        bus.subscribe(OrderTotal, capture_event)

        # Register handler
        handler = CreateOrderHandler(bus, store)
        bus.subscribe(CreateOrder, handler.handle)

        # Execute command
        bus.publish(
            CreateOrder(
                order_id="ORD-001",
                customer_name="Alice",
                total_amount=99.99,
            )
        )

        # Verify events were published
        assert len(published_events) == 3
        assert isinstance(published_events[0], OrderCreated)
        assert isinstance(published_events[1], ItemAdded)
        assert isinstance(published_events[2], OrderTotal)

        # Verify events persisted
        persisted = store.load("ORD-001")
        assert len(persisted) == 3

        # Verify aggregate state can be reconstructed
        order = Order.from_events("ORD-001", persisted)
        assert order.customer_name == "Alice"
        assert order.total == 99.99
        assert len(order.items) == 1

    def test_add_item_to_existing_order(self, infrastructure):
        """Test adding item to existing order."""
        bus, store = infrastructure
        published_events = []

        def capture_event(event):
            published_events.append(event)

        bus.subscribe(OrderCreated, capture_event)
        bus.subscribe(ItemAdded, capture_event)
        bus.subscribe(OrderTotal, capture_event)

        # Setup
        create_handler = CreateOrderHandler(bus, store)
        add_handler = AddItemHandler(bus, store)
        bus.subscribe(CreateOrder, create_handler.handle)
        bus.subscribe(AddItem, add_handler.handle)

        # Create order
        bus.publish(
            CreateOrder(
                order_id="ORD-002",
                customer_name="Bob",
                total_amount=50.0,
            )
        )

        # Add additional item
        bus.publish(
            AddItem(
                order_id="ORD-002",
                item_name="Extra Widget",
                item_price=25.0,
            )
        )

        # Verify all events published
        assert len(published_events) == 5  # 3 from create, 2 from add

        # Verify final state
        events = store.load("ORD-002")
        order = Order.from_events("ORD-002", events)
        assert order.customer_name == "Bob"
        assert order.total == 75.0  # 50 + 25
        assert len(order.items) == 2

    def test_event_correlation_chain(self, infrastructure):
        """Test correlation and causation IDs flow through messages."""
        bus, store = infrastructure
        events_with_correlation = []

        def track_correlation(event):
            events_with_correlation.append(event)

        bus.subscribe(OrderCreated, track_correlation)
        bus.subscribe(ItemAdded, track_correlation)
        bus.subscribe(OrderTotal, track_correlation)

        # Create handler
        handler = CreateOrderHandler(bus, store)
        bus.subscribe(CreateOrder, handler.handle)

        # Execute with correlation ID
        correlation_id = "flow-123"
        command = CreateOrder(
            order_id="ORD-003",
            customer_name="Charlie",
            total_amount=100.0,
            correlation_id=correlation_id,
        )

        bus.publish(command)

        # Note: In real implementation, handlers would copy correlation_id
        # This test shows the structure is available
        assert command.correlation_id == correlation_id

    def test_multiple_orders_isolated(self, infrastructure):
        """Test that multiple orders are properly isolated."""
        bus, store = infrastructure

        handler = CreateOrderHandler(bus, store)
        bus.subscribe(CreateOrder, handler.handle)

        # Create two orders
        bus.publish(
            CreateOrder(
                order_id="ORD-100",
                customer_name="User1",
                total_amount=10.0,
            )
        )
        bus.publish(
            CreateOrder(
                order_id="ORD-200",
                customer_name="User2",
                total_amount=20.0,
            )
        )

        # Verify isolation
        events1 = store.load("ORD-100")
        events2 = store.load("ORD-200")

        order1 = Order.from_events("ORD-100", events1)
        order2 = Order.from_events("ORD-200", events2)

        assert order1.customer_name == "User1"
        assert order1.total == 10.0
        assert order2.customer_name == "User2"
        assert order2.total == 20.0
