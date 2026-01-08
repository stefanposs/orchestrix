from dataclasses import dataclass
from orchestrix.core.messaging import Command, Event


@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    """Command to create a new order."""

    order_id: str
    amount: float


@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    """Event emitted when an order is created."""

    order_id: str
    amount: float


# Usage: CreateOrder is a command (intention), OrderCreated is an event (fact)
