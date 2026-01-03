"""Event store abstraction for Orchestrix.

The event store persists and retrieves domain events.
"""

from typing import Protocol

from orchestrix.message import Event


class EventStore(Protocol):
    """Event store for persisting domain events.

    The store is responsible for:
    - Saving events by aggregate ID
    - Loading event streams
    - Maintaining event order
    """

    def save(self, aggregate_id: str, events: list[Event]) -> None:
        """Save events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            events: List of events to persist
        """
        ...

    def load(self, aggregate_id: str) -> list[Event]:
        """Load all events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate

        Returns:
            List of events in chronological order
        """
        ...
