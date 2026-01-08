from dataclasses import dataclass
from orchestrix.core.common import Module
from orchestrix.core.eventsourcing import EventStore
from orchestrix.core.messaging import Message, MessageBus


@dataclass(frozen=True, kw_only=True)
class CreateOrder(Message):
    """Command to create a new order (demo)."""

    order_id: str
    amount: float


@dataclass(frozen=True, kw_only=True)
class OrderCreated(Message):
    """Event emitted when an order is created (demo)."""

    order_id: str
    amount: float


class EventsAndCommandsModule(Module):
    """Demo module for events and commands."""

    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register command and event handlers for the demo.

        Args:
            bus: The message bus.
            store: The event store (unused).
        """
        bus.subscribe(CreateOrder, lambda cmd: print(f"Command: {cmd}"))  # type: ignore
        bus.subscribe(OrderCreated, lambda evt: print(f"Event: {evt}, store: {store}"))  # type: ignore
