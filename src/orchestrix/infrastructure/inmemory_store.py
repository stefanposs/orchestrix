"""In-memory event store implementation.

Simple event store backed by a dictionary for development and testing.
"""

from collections import defaultdict

from orchestrix.logging import StructuredLogger, get_logger
from orchestrix.message import Event

_logger = StructuredLogger(get_logger(__name__))


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
        _logger.info(
            "Events saved",
            aggregate_id=aggregate_id,
            event_count=len(events),
        )

    def load(self, aggregate_id: str) -> list[Event]:
        """Load all events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate

        Returns:
            List of events in chronological order
        """
        events = list(self._events.get(aggregate_id, []))
        _logger.debug(
            "Events loaded",
            aggregate_id=aggregate_id,
            event_count=len(events),
        )
        return events
