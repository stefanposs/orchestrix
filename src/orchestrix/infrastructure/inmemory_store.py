"""In-memory event store implementation.

Simple event store backed by a dictionary for development and testing.
"""

from collections import defaultdict

from orchestrix.message import Event


class InMemoryEventStore:
    """In-memory event store.

    Stores events in memory by aggregate ID.
    Suitable for development, testing, and single-process applications.
    """

    def __init__(self) -> None:
        self._events: dict[str, list[Event]] = defaultdict(list)

    def save(self, aggregate_id: str, events: list[Event]) -> None:
        """Save events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            events: List of events to persist
        """
        self._events[aggregate_id].extend(events)

    def load(self, aggregate_id: str) -> list[Event]:
        """Load all events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate

        Returns:
            List of events in chronological order
        """
        return list(self._events.get(aggregate_id, []))
