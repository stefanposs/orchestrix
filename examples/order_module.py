"""
Order Module - Example Orchestrix module.

This module demonstrates:
- Aggregate: Order
- Commands: CreateOrder, CancelOrder
- Events: OrderCreated, OrderCancelled
- Command handlers with event persistence
- Event handlers for side effects
"""

from dataclasses import dataclass

from orchestrix import Command, Event, EventStore, MessageBus

# ============================================================================
# Commands
# ============================================================================


@dataclass(frozen=True)
class CreateOrder(Command):
    """Command to create a new order."""

    order_id: str
    customer_name: str
    total_amount: float


@dataclass(frozen=True)
class CancelOrder(Command):
    """Command to cancel an existing order."""

    order_id: str
    reason: str


# ============================================================================
# Events
# ============================================================================


@dataclass(frozen=True)
class OrderCreated(Event):
    """Event raised when an order is created."""

    order_id: str
    customer_name: str
    total_amount: float


@dataclass(frozen=True)
class OrderCancelled(Event):
    """Event raised when an order is cancelled."""

    order_id: str
    reason: str


# ============================================================================
# Aggregate
# ============================================================================


class Order:
    """
    Order aggregate.

    Enforces business rules and raises domain events.
    No I/O - pure domain logic.
    """

    def __init__(self, order_id: str):
        self.order_id = order_id
        self.customer_name: str = ""
        self.total_amount: float = 0.0
        self.is_cancelled: bool = False
        self._changes: list[Event] = []

    @staticmethod
    def create(order_id: str, customer_name: str, total_amount: float) -> "Order":
        """
        Factory method to create a new order.

        Args:
            order_id: Unique order identifier
            customer_name: Name of the customer
            total_amount: Total order amount

        Returns:
            New Order aggregate with OrderCreated event
        """
        order = Order(order_id)
        order._apply(
            OrderCreated(order_id=order_id, customer_name=customer_name, total_amount=total_amount)
        )
        return order

    def cancel(self, reason: str) -> None:
        """
        Cancel the order.

        Args:
            reason: Reason for cancellation

        Raises:
            ValueError: If order is already cancelled
        """
        if self.is_cancelled:
            raise ValueError(f"Order {self.order_id} is already cancelled")

        self._apply(OrderCancelled(order_id=self.order_id, reason=reason))

    def _apply(self, event: Event) -> None:
        """Apply an event to the aggregate state."""
        if isinstance(event, OrderCreated):
            self.customer_name = event.customer_name
            self.total_amount = event.total_amount
        elif isinstance(event, OrderCancelled):
            self.is_cancelled = True

        self._changes.append(event)

    def get_changes(self) -> list[Event]:
        """Get uncommitted events."""
        return list(self._changes)

    def clear_changes(self) -> None:
        """Clear uncommitted events."""
        self._changes.clear()


# ============================================================================
# Command Handlers
# ============================================================================


class CreateOrderHandler:
    """Handler for CreateOrder command."""

    def __init__(self, bus: MessageBus, store: EventStore):
        self.bus = bus
        self.store = store

    def handle(self, command: CreateOrder) -> None:
        """
        Handle CreateOrder command.

        Args:
            command: The CreateOrder command
        """
        # Create aggregate
        order = Order.create(
            order_id=command.order_id,
            customer_name=command.customer_name,
            total_amount=command.total_amount,
        )

        # Persist and publish events
        events = order.get_changes()
        self._persist_and_publish(command.order_id, events)
        order.clear_changes()

    def _persist_and_publish(self, aggregate_id: str, events: list[Event]) -> None:
        """Persist events and publish to bus."""
        self.store.save(aggregate_id, events)
        for event in events:
            self.bus.publish(event)


class CancelOrderHandler:
    """Handler for CancelOrder command."""

    def __init__(self, bus: MessageBus, store: EventStore):
        self.bus = bus
        self.store = store

    def handle(self, command: CancelOrder) -> None:
        """
        Handle CancelOrder command.

        Args:
            command: The CancelOrder command
        """
        # Load aggregate from event store
        events = self.store.load(command.order_id)
        if not events:
            raise ValueError(f"Order {command.order_id} not found")

        order = Order(command.order_id)
        for event in events:
            order._apply(event)
        order.clear_changes()

        # Execute command
        order.cancel(command.reason)

        # Persist and publish new events
        new_events = order.get_changes()
        self._persist_and_publish(command.order_id, new_events)
        order.clear_changes()

    def _persist_and_publish(self, aggregate_id: str, events: list[Event]) -> None:
        """Persist events and publish to bus."""
        self.store.save(aggregate_id, events)
        for event in events:
            self.bus.publish(event)


# ============================================================================
# Event Handlers
# ============================================================================


def on_order_created(event: OrderCreated) -> None:
    """
    Handle OrderCreated event.

    Example side effect: print notification.
    """
    print(f"📦 Order Created: {event.order_id}")
    print(f"   Customer: {event.customer_name}")
    print(f"   Amount: ${event.total_amount:.2f}")
    print()


def on_order_cancelled(event: OrderCancelled) -> None:
    """
    Handle OrderCancelled event.

    Example side effect: print notification.
    """
    print(f"❌ Order Cancelled: {event.order_id}")
    print(f"   Reason: {event.reason}")
    print()


# ============================================================================
# Module
# ============================================================================


class OrderModule:
    """
    Order module implementation.

    Registers all order-related components with the infrastructure.
    """

    def register(self, bus: MessageBus, store: EventStore) -> None:
        """
        Register order module components.

        Args:
            bus: Message bus for routing
            store: Event store for persistence
        """
        # Register command handlers
        create_handler = CreateOrderHandler(bus, store)
        cancel_handler = CancelOrderHandler(bus, store)

        bus.subscribe(CreateOrder, create_handler.handle)
        bus.subscribe(CancelOrder, cancel_handler.handle)

        # Register event handlers
        bus.subscribe(OrderCreated, on_order_created)
        bus.subscribe(OrderCancelled, on_order_cancelled)
