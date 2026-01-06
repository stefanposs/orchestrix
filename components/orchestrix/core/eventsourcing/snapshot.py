"""Event Store snapshots for efficient event sourcing.

Snapshots allow fast reconstruction of aggregate state without replaying all events.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class Snapshot:
    """A snapshot of an aggregate's state at a specific version.

    Attributes:
        aggregate_id: The ID of the aggregate
        aggregate_type: The type/class name of the aggregate
        version: The version number (number of events) at snapshot time
        state: The serialized state (typically JSON-compatible dict)
        timestamp: When the snapshot was created
    """

    aggregate_id: str
    aggregate_type: str
    version: int
    state: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventStore(Protocol):
    """Event store with snapshot support.

    Snapshots optimize event stream reconstruction by caching aggregate state
    at specific version points. Instead of replaying 1000 events, load the
    snapshot at version 950 + 50 remaining events.
    """

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save a snapshot of aggregate state.

        Args:
            snapshot: The snapshot to persist
        """
        ...

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Load the latest snapshot for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate

        Returns:
            The latest snapshot, or None if no snapshot exists
        """
        ...

    def save(self, aggregate_id: str, events: list[Any]) -> None:
        """Save events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            events: List of events to persist
        """
        ...

    def load(self, aggregate_id: str, from_version: int = 0) -> list[Any]:
        """Load events for an aggregate.

        Args:
            aggregate_id: The ID of the aggregate
            from_version: Load events from this version onwards

        Returns:
            List of events in chronological order
        """
        ...
