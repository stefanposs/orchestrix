"""Async event store abstraction for Orchestrix.

Non-blocking event persistence for async applications.
"""

from collections import defaultdict

from orchestrix.logging import StructuredLogger, get_logger
from orchestrix.message import Event

_logger = StructuredLogger(get_logger(__name__))


class InMemoryAsyncEventStore:
    """In-memory async event store.

    Persists and retrieves event streams asynchronously.
    Suitable for async applications, FastAPI, Starlette, and other async frameworks.
    """

    def __init__(self) -> None:
        """Initialize async event store."""
        self._events: dict[str, list[Event]] = defaultdict(list)

    async def save(self, aggregate_id: str, events: list[Event]) -> None:
        """Save events for an aggregate asynchronously.

        Args:
            aggregate_id: The ID of the aggregate
            events: List of events to persist
        """
        self._events[aggregate_id].extend(events)
        _logger.info(
            "Events saved (async)",
            aggregate_id=aggregate_id,
            event_count=len(events),
        )

    async def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]:
        """Load events for an aggregate asynchronously.

        Args:
            aggregate_id: The ID of the aggregate
            from_version: Load events from this version onwards (default: 0)

        Returns:
            List of events in chronological order
        """
        events = list(self._events.get(aggregate_id, []))
        result = events[from_version:]
        _logger.debug(
            "Events loaded (async)",
            aggregate_id=aggregate_id,
            from_version=from_version,
            event_count=len(result),
        )
        return result
