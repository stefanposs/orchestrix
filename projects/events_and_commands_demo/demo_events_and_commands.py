from dataclasses import dataclass
from orchestrix import Command, Event

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    amount: float

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    amount: float

# Usage: CreateOrder is a command (intention), OrderCreated is an event (fact)
