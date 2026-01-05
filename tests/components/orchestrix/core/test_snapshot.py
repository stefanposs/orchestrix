"""Tests for snapshot store protocol and implementations."""

import pytest
from orchestrix.core.eventsourcing.snapshot import Snapshot


class FakeSnapshotStore:
    """Fake snapshot store for testing."""

    def __init__(self) -> None:
        """Initialize fake snapshot store."""
        self._snapshots: dict[str, Snapshot] = {}

    async def save_snapshot_async(self, snapshot: Snapshot) -> None:
        """Save a snapshot."""
        self._snapshots[snapshot.aggregate_id] = snapshot

    async def load_snapshot_async(self, aggregate_id: str) -> Snapshot | None:
        """Load a snapshot."""
        return self._snapshots.get(aggregate_id)

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Sync save (not recommended)."""
        self._snapshots[snapshot.aggregate_id] = snapshot

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Sync load (not recommended)."""
        return self._snapshots.get(aggregate_id)


@pytest.fixture
def snapshot_store():
    """Provide fake snapshot store."""
    return FakeSnapshotStore()


@pytest.fixture
def sample_snapshot():
    """Create sample snapshot."""
    return Snapshot(
        aggregate_id="order-123",
        aggregate_type="Order",
        version=10,
        state={"status": "processing", "items": [{"id": "item-1", "qty": 5}]},
    )


# Test Snapshot Protocol


@pytest.mark.asyncio
async def test_save_snapshot(snapshot_store, sample_snapshot):
    """Test saving a snapshot."""
    await snapshot_store.save_snapshot_async(sample_snapshot)

    # Verify by loading
    loaded = await snapshot_store.load_snapshot_async(sample_snapshot.aggregate_id)

    assert loaded is not None
    assert loaded.aggregate_id == sample_snapshot.aggregate_id
    assert loaded.version == 10


@pytest.mark.asyncio
async def test_load_nonexistent_snapshot(snapshot_store):
    """Test that loading non-existent snapshot returns None."""
    result = await snapshot_store.load_snapshot_async("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_snapshot_state_preserved(snapshot_store):
    """Test that snapshot state is fully preserved."""
    state = {"status": "completed", "items": [{"id": "1"}, {"id": "2"}], "nested": {"key": "value"}}
    snapshot = Snapshot(aggregate_id="order-456", aggregate_type="Order", version=15, state=state)

    await snapshot_store.save_snapshot_async(snapshot)
    loaded = await snapshot_store.load_snapshot_async("order-456")

    assert loaded.state == state
    assert loaded.state["nested"]["key"] == "value"


@pytest.mark.asyncio
async def test_snapshot_version_tracking(snapshot_store):
    """Test that snapshot versions are tracked."""
    snap1 = Snapshot(aggregate_id="order-789", aggregate_type="Order", version=5, state={"v": 1})
    snap2 = Snapshot(aggregate_id="order-789", aggregate_type="Order", version=10, state={"v": 2})

    # Save both (v2 should overwrite v1)
    await snapshot_store.save_snapshot_async(snap1)
    await snapshot_store.save_snapshot_async(snap2)

    # Load should return latest
    loaded = await snapshot_store.load_snapshot_async("order-789")

    assert loaded.version == 10
    assert loaded.state["v"] == 2


@pytest.mark.asyncio
async def test_multiple_aggregates(snapshot_store):
    """Test snapshots for different aggregates."""
    snap1 = Snapshot(
        aggregate_id="order-1",
        aggregate_type="Order",
        version=5,
        state={"order_id": "1"},
    )
    snap2 = Snapshot(
        aggregate_id="order-2",
        aggregate_type="Order",
        version=3,
        state={"order_id": "2"},
    )

    await snapshot_store.save_snapshot_async(snap1)
    await snapshot_store.save_snapshot_async(snap2)

    loaded1 = await snapshot_store.load_snapshot_async("order-1")
    loaded2 = await snapshot_store.load_snapshot_async("order-2")

    assert loaded1.state["order_id"] == "1"
    assert loaded2.state["order_id"] == "2"


# Sync API Tests


def test_sync_save_snapshot(snapshot_store, sample_snapshot):
    """Test synchronous snapshot save."""
    snapshot_store.save_snapshot(sample_snapshot)

    loaded = snapshot_store.load_snapshot(sample_snapshot.aggregate_id)

    assert loaded is not None
    assert loaded.aggregate_id == sample_snapshot.aggregate_id


def test_sync_load_nonexistent(snapshot_store):
    """Test synchronous load of non-existent snapshot."""
    result = snapshot_store.load_snapshot("nonexistent")

    assert result is None
