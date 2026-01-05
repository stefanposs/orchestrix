"""Async event store abstraction for Orchestrix.

Non-blocking event persistence for async applications.
"""

from collections import defaultdict
from collections.abc import Sequence

from orchestrix.core.common.exceptions import ConcurrencyError
from orchestrix.core.common.logging import StructuredLogger, get_logger
from orchestrix.core.eventsourcing.snapshot import Snapshot
from orchestrix.core.messaging.message import Event

_logger = StructuredLogger(get_logger(__name__))


class InMemoryAsyncEventStore:
    """In-memory async event store with snapshot support."""

    def __init__(self) -> None:
        self._events: dict[str, list[Event]] = defaultdict(list)
        self._snapshots: dict[str, Snapshot] = {}

    async def save(
        self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None
    ) -> None:
        """Save events for an aggregate asynchronously.

        Args:
            aggregate_id: The ID of the aggregate
            events: List of events to persist
            expected_version: Expected current version for optimistic locking.
                If provided and doesn't match actual version, raises ConcurrencyError.

        Raises:
            ConcurrencyError: If expected_version doesn't match actual version
        """
        if expected_version is not None:
            current_version = len(self._events[aggregate_id]) - 1
            if current_version != expected_version:
                raise ConcurrencyError(
                    aggregate_id=aggregate_id,
                    expected_version=expected_version,
                    actual_version=current_version,
                )

        self._events[aggregate_id].extend(events)
        _logger.info(
            "Events saved (async)",
            aggregate_id=aggregate_id,
            event_count=len(events),
        )

    async def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]:
        """Load events for an aggregate asynchronously."""
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
        """Save a snapshot asynchronously."""
        self._snapshots[snapshot.aggregate_id] = snapshot
        _logger.info(
            "Snapshot saved (async)",
            aggregate_id=snapshot.aggregate_id,
            version=snapshot.version,
        )

    async def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Load the latest snapshot asynchronously."""
        snapshot = self._snapshots.get(aggregate_id)
        if snapshot:
            _logger.debug(
                "Snapshot loaded (async)",
                aggregate_id=aggregate_id,
                version=snapshot.version,
            )
        return snapshot
