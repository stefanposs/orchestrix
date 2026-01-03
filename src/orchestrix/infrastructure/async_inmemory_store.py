"""Async event store abstraction for Orchestrix.

Non-blocking event persistence for async applications.
"""

from collections import defaultdict

from orchestrix.core.logging import StructuredLogger, get_logger
from orchestrix.core.message import Event
from orchestrix.core.snapshot import Snapshot

_logger = StructuredLogger(get_logger(__name__))


class InMemoryAsyncEventStore:
    """In-memory async event store with snapshot support.

    Persists and retrieves event streams asynchronously.
    Snapshots can be used to optimize event stream reconstruction.
    Suitable for async applications, FastAPI, Starlette, and other async frameworks.
    """

    def __init__(self) -> None:
        """Initialize async event store."""
        self._events: dict[str, list[Event]] = defaultdict(list)
        self._snapshots: dict[str, Snapshot] = {}

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

    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save a snapshot asynchronously.

        Args:
            snapshot: The snapshot to persist
        """
        self._snapshots[snapshot.aggregate_id] = snapshot
        _logger.info(
            "Snapshot saved (async)",
            aggregate_id=snapshot.aggregate_id,
            version=snapshot.version,
        )

    async def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Load the latest snapshot asynchronously.

        Args:
            aggregate_id: The ID of the aggregate

        Returns:
            The latest snapshot, or None if no snapshot exists
        """
        snapshot = self._snapshots.get(aggregate_id)
        if snapshot:
            _logger.debug(
                "Snapshot loaded (async)",
                aggregate_id=aggregate_id,
                version=snapshot.version,
            )
        return snapshot
