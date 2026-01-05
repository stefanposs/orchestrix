"""Tests for PostgreSQL event store implementation.

Uses pytest-asyncio for async tests and testcontainers for isolated PostgreSQL instances.
"""

import contextlib
import json
import json as _json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from testcontainers.postgres import PostgresContainer

# Conditional import for PostgreSQL support
pytest.importorskip("asyncpg", reason="asyncpg not installed - skip postgres tests")

from orchestrix.core.eventsourcing.snapshot import Snapshot
from orchestrix.core.messaging.message import Event
from orchestrix.infrastructure.postgres.store import PostgreSQLEventStore


@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    """Test event: Order created."""

    order_id: str
    customer_id: str
    total: float


@dataclass(frozen=True, kw_only=True)
class OrderShipped(Event):
    """Test event: Order shipped."""

    order_id: str
    tracking_number: str


# Use testcontainers for isolated Postgres


# Parametrize over all Postgres versions in .container-versions.json
def _get_postgres_versions():
    # Suche das Projekt-Root relativ zu dieser Datei
    root = Path(__file__).resolve().parents[4]
    config_path = root / ".container-versions.json"
    with config_path.open() as f:
        return _json.load(f)["postgres"]


import pytest


@pytest.fixture(params=_get_postgres_versions())
def postgres_container(request):
    """Start a Postgres container for each version in the list."""
    version = request.param
    with PostgresContainer(f"postgres:{version}") as container:
        container.start()
        dsn = container.get_connection_url()
        # testcontainers liefert postgresql+psycopg2://..., asyncpg braucht postgresql://
        if dsn.startswith("postgresql+psycopg2://"):
            dsn = dsn.replace("postgresql+psycopg2://", "postgresql://", 1)
        yield dsn


@pytest.fixture
async def store(postgres_container):
    """Create and initialize PostgreSQL event store (using testcontainer)."""
    store = PostgreSQLEventStore(
        connection_string=postgres_container, pool_min_size=2, pool_max_size=5
    )
    await store.initialize()

    # Clean up tables before each test
    assert store._pool is not None
    async with store._pool.acquire() as conn:
        await conn.execute("DELETE FROM events")
        await conn.execute("DELETE FROM snapshots")

    yield store

    # Cleanup
    if store._pool:
        await store._pool.close()


@pytest.fixture
def aggregate_id():
    """Generate unique aggregate ID."""
    return f"order-{uuid.uuid4()}"


@pytest.fixture
def sample_events(aggregate_id):
    """Create sample events for testing."""
    return [
        Event(
            id=str(uuid.uuid4()),
            type="OrderCreated",
            source="/orders/service",
            subject=aggregate_id,
            data=OrderCreated(order_id=aggregate_id, customer_id="customer-123", total=99.99),
            timestamp=datetime.now(UTC),
        ),
        Event(
            id=str(uuid.uuid4()),
            type="OrderShipped",
            source="/orders/service",
            subject=aggregate_id,
            data=OrderShipped(order_id=aggregate_id, tracking_number="TRACK-456"),
            timestamp=datetime.now(UTC),
        ),
    ]


# ========================================
# Basic Operations Tests
# ========================================


@pytest.mark.asyncio
async def test_save_and_load_events(store, aggregate_id, sample_events):
    """Test saving and loading events."""
    # Save events
    await store.save(aggregate_id, sample_events)

    # Load events
    loaded = await store.load(aggregate_id)

    assert len(loaded) == 2
    assert loaded[0].type == "OrderCreated"
    assert loaded[1].type == "OrderShipped"
    assert loaded[0].subject == aggregate_id
    assert loaded[1].subject == aggregate_id


@pytest.mark.asyncio
async def test_load_events_from_version(store, aggregate_id, sample_events):
    """Test loading events starting from specific version."""
    # Save 3 batches of events
    await store.save(aggregate_id, [sample_events[0]])
    await store.save(aggregate_id, [sample_events[1]])
    third_event = Event(
        id=str(uuid.uuid4()),
        type="OrderCancelled",
        source="/orders/service",
        subject=aggregate_id,
        data={"reason": "customer request"},
        timestamp=datetime.now(UTC),
    )
    await store.save(aggregate_id, [third_event])

    # Load from version 0 (should return events 1 and 2)
    loaded = await store.load(aggregate_id, from_version=0)

    assert len(loaded) == 2
    assert loaded[0].type == "OrderShipped"
    assert loaded[1].type == "OrderCancelled"


@pytest.mark.asyncio
async def test_load_nonexistent_aggregate(store):
    """Test loading events for non-existent aggregate returns empty list."""
    events = await store.load("nonexistent-id")
    assert events == []


# ========================================
# Concurrency Tests
# ========================================


@pytest.mark.asyncio
async def test_optimistic_concurrency_conflict(store, aggregate_id, sample_events):
    """Test that saving duplicate versions raises error."""
    # Save first event
    await store.save(aggregate_id, [sample_events[0]])

    # Manually create event with version 1
    duplicate_event = Event(
        id=str(uuid.uuid4()),
        type="DuplicateEvent",
        source="/test",
        subject=aggregate_id,
        data={"test": "data"},
        timestamp=datetime.now(UTC),
    )

    # Try to insert duplicate version (should fail)
    with pytest.raises(Exception) as exc_info:
        async with store._pool.acquire() as conn, conn.transaction():
            await conn.execute(
                """
                INSERT INTO events (
                    aggregate_id, version, event_id, event_type,
                    event_source, event_subject, event_data, event_time
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                aggregate_id,
                0,  # Duplicate version
                duplicate_event.id,
                duplicate_event.type,
                duplicate_event.source,
                duplicate_event.subject,
                json.dumps({}),
                duplicate_event.timestamp,
            )

    # Should raise unique constraint violation
    assert "unique" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_concurrent_saves_different_aggregates(store, sample_events):
    """Test that concurrent saves to different aggregates work."""
    aggregate_1 = f"order-{uuid.uuid4()}"
    aggregate_2 = f"order-{uuid.uuid4()}"

    # Save to both aggregates concurrently
    event1 = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders/service",
        subject=aggregate_1,
        data={"order_id": aggregate_1},
        timestamp=datetime.now(UTC),
    )
    event2 = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders/service",
        subject=aggregate_2,
        data={"order_id": aggregate_2},
        timestamp=datetime.now(UTC),
    )
    await store.save(aggregate_1, [event1])
    await store.save(aggregate_2, [event2])

    # Both should succeed
    events_1 = await store.load(aggregate_1)
    events_2 = await store.load(aggregate_2)

    assert len(events_1) == 1
    assert len(events_2) == 1
    assert events_1[0].subject == aggregate_1
    assert events_2[0].subject == aggregate_2


# ========================================
# Snapshot Tests
# ========================================


@pytest.mark.asyncio
async def test_save_and_load_snapshot(store, aggregate_id):
    """Test saving and loading snapshots."""
    snapshot = Snapshot(
        aggregate_id=aggregate_id,
        aggregate_type="Order",
        version=5,
        state={"order_status": "shipped"},
    )

    # Save snapshot
    await store.save_snapshot_async(snapshot)

    # Load snapshot
    loaded = await store.load_snapshot_async(aggregate_id)

    assert loaded is not None
    assert loaded.aggregate_id == aggregate_id
    assert loaded.aggregate_type == "Order"
    assert loaded.version == 5
    assert loaded.state == {"order_status": "shipped"}


@pytest.mark.asyncio
async def test_snapshot_upsert(store, aggregate_id):
    """Test that saving snapshot twice updates existing record."""
    # Save first snapshot
    snapshot_1 = Snapshot(
        aggregate_id=aggregate_id,
        aggregate_type="Order",
        version=3,
        state={"status": "pending"},
    )
    await store.save_snapshot_async(snapshot_1)

    # Update snapshot
    snapshot_2 = Snapshot(
        aggregate_id=aggregate_id,
        aggregate_type="Order",
        version=7,
        state={"status": "completed"},
    )
    await store.save_snapshot_async(snapshot_2)

    # Load should return latest
    loaded = await store.load_snapshot_async(aggregate_id)

    assert loaded is not None
    assert loaded.version == 7
    assert loaded.state == {"status": "completed"}


@pytest.mark.asyncio
async def test_load_nonexistent_snapshot(store):
    """Test loading snapshot for non-existent aggregate returns None."""
    snapshot = await store.load_snapshot_async("nonexistent-id")
    assert snapshot is None


# ========================================
# Metadata Tests
# ========================================


@pytest.mark.asyncio
async def test_event_metadata_preserved(store, aggregate_id):
    """Test that all event metadata is preserved."""
    event = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders/service",
        subject=aggregate_id,
        data={"order_id": aggregate_id},
        timestamp=datetime.now(UTC),
        specversion="1.0",
        datacontenttype="application/json",
        dataschema="https://example.com/schema",
        correlation_id="corr-123",
        causation_id="cause-456",
    )

    await store.save(aggregate_id, [event])
    loaded = await store.load(aggregate_id)

    assert len(loaded) == 1
    saved_event = loaded[0]
    assert saved_event.id == event.id
    assert saved_event.type == event.type
    assert saved_event.source == event.source
    assert saved_event.specversion == event.specversion
    assert saved_event.datacontenttype == event.datacontenttype
    assert saved_event.dataschema == event.dataschema
    assert saved_event.correlation_id == event.correlation_id
    assert saved_event.causation_id == event.causation_id


# ========================================
# Health Check Tests
# ========================================


@pytest.mark.asyncio
async def test_ping_success(store):
    """Test that ping returns True when database is accessible."""
    result = await store.ping()
    assert result is True


@pytest.mark.asyncio
async def test_ping_failure():
    """Test that ping returns False when database is not accessible."""
    store = PostgreSQLEventStore(connection_string="postgresql://invalid:5432/nonexistent")

    with contextlib.suppress(Exception):
        await store.initialize()

    result = await store.ping()
    assert result is False


# ========================================
# Edge Cases
# ========================================


@pytest.mark.asyncio
async def test_save_empty_events_list(store, aggregate_id):
    """Test that saving empty events list is no-op."""
    await store.save(aggregate_id, [])

    events = await store.load(aggregate_id)
    assert events == []


@pytest.mark.asyncio
async def test_large_event_data(store, aggregate_id):
    """Test saving and loading events with large payloads."""
    large_data = {"items": [{"id": i, "name": f"item-{i}"} for i in range(1000)]}
    event = Event(
        id=str(uuid.uuid4()),
        type="LargeOrder",
        source="/orders",
        subject=aggregate_id,
        data=large_data,
        timestamp=datetime.now(UTC),
    )

    await store.save(aggregate_id, [event])
    loaded = await store.load(aggregate_id)

    assert len(loaded) == 1
    assert loaded[0].data == large_data


@pytest.mark.asyncio
async def test_unicode_in_event_data(store, aggregate_id):
    """Test that unicode characters in event data are preserved."""
    event = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders",
        subject=aggregate_id,
        data={"customer_name": "Müller 日本 🎉"},
        timestamp=datetime.now(UTC),
    )

    await store.save(aggregate_id, [event])
    loaded = await store.load(aggregate_id)

    assert loaded[0].data["customer_name"] == "Müller 日本 🎉"
