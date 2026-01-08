from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrix.core.eventsourcing.event_store import EventStore
    from orchestrix.core.messaging.message_bus import MessageBus
    from orchestrix.core.common.module import Module
    from orchestrix.core.messaging.message import Message


@dataclass(frozen=True, kw_only=True)
class MyCommand(Message):
    """Demo command for tracing."""

    value: int


@dataclass(frozen=True, kw_only=True)
class MyEvent(Message):
    """Demo event for tracing."""

    value: int


class TracingModule(Module):
    """Demo module for tracing commands and events."""

    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register tracing handlers for commands and events.

        Args:
            bus: The message bus.
            store: The event store (unused).
        """
        bus.subscribe(
            MyCommand, lambda cmd: print(f"TRACE: Command {cmd}")
        )  # Subscribe to MyCommand
        bus.subscribe(MyEvent, lambda evt: print(f"TRACE: Event {evt}"))  # Subscribe to MyEvent
