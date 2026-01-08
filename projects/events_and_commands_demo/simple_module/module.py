from orchestrix import Module, MessageBus, EventStore
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class CreateOrder:
    order_id: str
    amount: float

@dataclass(frozen=True, kw_only=True)
class OrderCreated:
    order_id: str
    amount: float

class EventsAndCommandsModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(CreateOrder, lambda cmd: print(f"Command: {cmd}"))
        bus.subscribe(OrderCreated, lambda evt: print(f"Event: {evt}"))
