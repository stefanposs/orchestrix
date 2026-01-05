"""Event store abstraction for Orchestrix.

The event store persists and retrieves domain events.
"""

from collections.abc import Sequence
from typing import Protocol

from orchestrix.core.messaging.message import Event


class EventStore(Protocol):
    """Event store for persisting domain events.

    The store is responsible for:
    - Saving events by aggregate ID
    - Loading event streams
    - Maintaining event order
    - Optimistic concurrency control via expected_version
    """

    def save(
        self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None
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

    def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]:
        """Load all events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            from_version: Load events from this version onwards (default: 0)

        Returns:
            List of events in chronological order
        """
        ...


class AsyncEventStore(Protocol):
    """Async event store for persisting domain events."""

    async def save(
        self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None
    ) -> None:
        """Save events for an aggregate asynchronously."""
        ...

    async def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]:
        """Load all events for an aggregate asynchronously."""
        ...
