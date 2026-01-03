"""Command handler base class for Orchestrix.

Command handlers process commands and persist resulting events.
"""

from typing import Protocol

from orchestrix.core.event_store import EventStore
from orchestrix.core.message import Command, Event
from orchestrix.core.message_bus import MessageBus


class CommandHandler(Protocol):
    """Base protocol for command handlers.

    Command handlers:
    - Process commands
    - Persist resulting events to event store
    - Publish events via message bus
    """

    def __init__(self, bus: MessageBus, store: EventStore):
        """Initialize handler with infrastructure dependencies.

        Args:
            bus: Message bus for publishing events
            store: Event store for persisting events
        """
        ...

    def handle(self, command: Command) -> None:
        """Handle a command.

        Args:
            command: The command to process
        """
        ...

    def _persist_and_publish(self, aggregate_id: str, events: list[Event]) -> None:
        """Persist events to store and publish via bus.

        Args:
            aggregate_id: The ID of the aggregate
            events: Events to persist and publish
        """
        ...
