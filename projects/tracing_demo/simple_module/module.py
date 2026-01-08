from orchestrix import Module, MessageBus, EventStore
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class MyCommand:
    value: int

@dataclass(frozen=True, kw_only=True)
class MyEvent:
    value: int

class TracingModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(MyCommand, lambda cmd: print(f"TRACE: Command {cmd}"))
        bus.subscribe(MyEvent, lambda evt: print(f"TRACE: Event {evt}"))
