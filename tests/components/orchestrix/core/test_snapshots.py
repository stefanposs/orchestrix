"""Tests for event store snapshots."""

import pytest
from orchestrix.core.eventsourcing.snapshot import Snapshot
from orchestrix.core.messaging.message import Event
from orchestrix.infrastructure.memory.store import InMemoryEventStore


class UserCreated(Event):
    """Test event."""

    user_id: str = "user-123"


class UserUpdated(Event):
    """Test event."""

    user_id: str = "user-123"


@pytest.fixture
def store():
    """Provide a fresh event store with snapshot support."""
    return InMemoryEventStore()


class TestSnapshots:
    """Test snapshot functionality."""

    def test_save_and_load_snapshot(self, store):
        """Test saving and loading a snapshot."""
        aggregate_id = "agg-001"
        state = {"user_id": "user-123", "name": "Alice", "email": "alice@example.com"}

        snapshot = Snapshot(
            aggregate_id=aggregate_id,
            aggregate_type="User",
            version=100,
            state=state,
        )

        store.save_snapshot(snapshot)
        loaded = store.load_snapshot(aggregate_id)

        assert loaded is not None
        assert loaded.aggregate_id == aggregate_id
        assert loaded.version == 100
        assert loaded.state == state

    def test_load_nonexistent_snapshot(self, store):
        """Test loading snapshot for aggregate without snapshot."""
        loaded = store.load_snapshot("nonexistent")

        assert loaded is None

    def test_snapshot_replaces_previous(self, store):
        """Test that saving new snapshot replaces the old one."""
        aggregate_id = "agg-002"

        # First snapshot
        snapshot1 = Snapshot(
            aggregate_id=aggregate_id,
            aggregate_type="User",
            version=50,
            state={"version": 1},
        )
        store.save_snapshot(snapshot1)

        # Second snapshot
        snapshot2 = Snapshot(
            aggregate_id=aggregate_id,
            aggregate_type="User",
            version=100,
            state={"version": 2},
        )
        store.save_snapshot(snapshot2)

        loaded = store.load_snapshot(aggregate_id)

        # Should have the latest snapshot
        assert loaded.version == 100
        assert loaded.state == {"version": 2}

    def test_load_events_from_snapshot_version(self, store):
        """Test loading events starting from snapshot version."""
        aggregate_id = "agg-003"

        # Save 5 events
        events = [UserCreated(), UserUpdated(), UserCreated(), UserUpdated(), UserCreated()]
        store.save(aggregate_id, events)

        # Create snapshot at version 2
        snapshot = Snapshot(
            aggregate_id=aggregate_id,
            aggregate_type="User",
            version=2,
            state={"snapshot": "state"},
        )
        store.save_snapshot(snapshot)

        # Load events from snapshot version (version 2 onwards)
        remaining_events = store.load(aggregate_id, from_version=snapshot.version)

        # Should load events starting from version 2 (3 events remaining)
        assert len(remaining_events) == 3
        assert remaining_events[0].type == "UserCreated"

    def test_snapshot_optimization_pattern(self, store):
        """Test the snapshot optimization pattern."""
        aggregate_id = "agg-004"

        # Create 1000 events
        events = [UserCreated() if i % 2 == 0 else UserUpdated() for i in range(1000)]
        store.save(aggregate_id, events)

        # At version 950, create snapshot
        snapshot_state = {"aggregate_state": "at_version_950"}
        snapshot = Snapshot(
            aggregate_id=aggregate_id,
            aggregate_type="User",
            version=950,
            state=snapshot_state,
        )
        store.save_snapshot(snapshot)

        # Later, load aggregate: load snapshot + remaining 50 events
        snapshot = store.load_snapshot(aggregate_id)
        assert snapshot is not None

        remaining_events = store.load(aggregate_id, from_version=snapshot.version)

        assert len(remaining_events) == 50
        assert snapshot.state == snapshot_state

    def test_snapshots_isolated_per_aggregate(self, store):
        """Test that snapshots are isolated per aggregate."""
        agg1 = "agg-a"
        agg2 = "agg-b"

        snapshot1 = Snapshot(
            aggregate_id=agg1,
            aggregate_type="Type1",
            version=100,
            state={"agg": "a"},
        )

        snapshot2 = Snapshot(
            aggregate_id=agg2,
            aggregate_type="Type2",
            version=200,
            state={"agg": "b"},
        )

        store.save_snapshot(snapshot1)
        store.save_snapshot(snapshot2)

        loaded1 = store.load_snapshot(agg1)
        loaded2 = store.load_snapshot(agg2)

        assert loaded1.state == {"agg": "a"}
        assert loaded2.state == {"agg": "b"}

    def test_snapshot_preserves_all_metadata(self, store):
        """Test that snapshot preserves all metadata."""
        aggregate_id = "agg-005"
        state = {"key": "value"}

        snapshot = Snapshot(
            aggregate_id=aggregate_id,
            aggregate_type="CustomType",
            version=42,
            state=state,
        )

        store.save_snapshot(snapshot)
        loaded = store.load_snapshot(aggregate_id)

        assert loaded.aggregate_id == aggregate_id
        assert loaded.aggregate_type == "CustomType"
        assert loaded.version == 42
        assert loaded.state == state
        assert loaded.timestamp is not None
