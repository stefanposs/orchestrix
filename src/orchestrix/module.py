"""Module abstraction for Orchestrix.

Modules encapsulate domain logic and register their components.
"""

from typing import Protocol


class Module(Protocol):
    """A module encapsulates domain logic and component registration.

    Modules register:
    - Command handlers
    - Event handlers
    - Aggregates
    - Domain services
    """

    def register(self, bus: "MessageBus", store: "EventStore") -> None:
        """Register module components with the infrastructure.

        Args:
            bus: Message bus for publishing and subscribing
            store: Event store for persisting domain events
        """
        ...


# Import types for type hints
from orchestrix.event_store import EventStore
from orchestrix.message_bus import MessageBus
