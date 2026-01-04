"""Event store abstraction for Orchestrix.

The event store persists and retrieves domain events.
"""

from typing import Protocol

from orchestrix.core.message import Event


class EventStore(Protocol):
    """Event store for persisting domain events.

    The store is responsible for:
    - Saving events by aggregate ID
    - Loading event streams
    - Maintaining event order
    - Optimistic concurrency control via expected_version
    """

    def save(
        self, aggregate_id: str, events: list[Event], expected_version: int | None = None
    ) -> None:
        """Save events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            events: List of events to persist
            expected_version: Expected current version for optimistic locking.
                If provided and doesn't match actual version, raises ConcurrencyError.

        Raises:
            ConcurrencyError: If expected_version doesn't match actual version
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
