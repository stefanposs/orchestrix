"""In-memory event store implementation.

Simple event store backed by a dictionary for development and testing.
"""

from collections import defaultdict

from orchestrix.core.logging import StructuredLogger, get_logger
from orchestrix.core.message import Event
from orchestrix.core.snapshot import Snapshot

_logger = StructuredLogger(get_logger(__name__))


class InMemoryEventStore:
    """In-memory event store with snapshot support.

    Stores events in memory by aggregate ID.
    Snapshots can be used to optimize event stream reconstruction.
    Suitable for development, testing, and single-process applications.
    """

    def __init__(self) -> None:
        self._events: dict[str, list[Event]] = defaultdict(list)
        self._snapshots: dict[str, Snapshot] = {}

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

    def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]:
        """Load events for an aggregate from a specific version.

        Args:
            aggregate_id: The ID of the aggregate
            from_version: Load events from this version onwards (default: 0)

        Returns:
            List of events in chronological order
        """
        events = list(self._events.get(aggregate_id, []))
        result = events[from_version:]
        _logger.debug(
            "Events loaded",
            aggregate_id=aggregate_id,
            from_version=from_version,
            event_count=len(result),
        )
        return result

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save a snapshot of aggregate state.

        Args:
            snapshot: The snapshot to persist
        """
        self._snapshots[snapshot.aggregate_id] = snapshot
        _logger.info(
            "Snapshot saved",
            aggregate_id=snapshot.aggregate_id,
            version=snapshot.version,
        )

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Load the latest snapshot for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate

        Returns:
            The latest snapshot, or None if no snapshot exists
        """
        snapshot = self._snapshots.get(aggregate_id)
        if snapshot:
            _logger.debug(
                "Snapshot loaded",
                aggregate_id=aggregate_id,
                version=snapshot.version,
            )
        return snapshot
