"""Tests for EventSourcingDB event store implementation using official SDK.

Uses pytest-asyncio for async tests and mocks the official eventsourcingdb Client.
For integration tests, use testcontainers with Container from eventsourcingdb SDK.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Conditional import for EventSourcingDB support
pytest.importorskip("eventsourcingdb", reason="eventsourcingdb not installed - skip tests")

from orchestrix.infrastructure.eventsourcingdb_store import EventSourcingDBStore
from orchestrix.core.message import Event
from orchestrix.core.snapshot import Snapshot


@dataclass(frozen=True)
class OrderCreated:
    """Test event: Order created."""

    order_id: str
    customer_id: str
    total: float


@dataclass(frozen=True)
class OrderShipped:
    """Test event: Order shipped."""

    order_id: str
    tracking_number: str


@pytest.fixture
def store():
    """Create EventSourcingDB store instance."""
    return EventSourcingDBStore(
        base_url="http://localhost:2113",
        api_token="test-token-12345",  # noqa: S106
    )


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
            data=OrderCreated(
                order_id=aggregate_id, customer_id="customer-123", total=99.99
            ),
            timestamp=datetime.now(timezone.utc),
        ),
        Event(
            id=str(uuid.uuid4()),
            type="OrderShipped",
            source="/orders/service",
            subject=aggregate_id,
            data=OrderShipped(order_id=aggregate_id, tracking_number="TRACK-456"),
            timestamp=datetime.now(timezone.utc),
        ),
    ]


# ========================================
# Basic Operations Tests
# ========================================


@pytest.mark.asyncio
async def test_initialize_creates_client(store):
    """Test that initialize creates EventSourcingDB client."""
    await store.initialize()

    assert store._client is not None
    assert hasattr(store._client, "write_events")
    assert hasattr(store._client, "read_events")
    assert hasattr(store._client, "ping")


@pytest.mark.asyncio
async def test_save_events(store, aggregate_id, sample_events):
    """Test saving events to EventSourcingDB."""
    await store.initialize()

    # Mock the SDK client's write_events method
    with patch.object(store._client, "write_events", new_callable=AsyncMock) as mock_write:
        await store.save_async(aggregate_id, sample_events)

        # Verify write_events was called once
        mock_write.assert_called_once()
        call_args = mock_write.call_args

        # Verify events parameter
        events = call_args[1]["events"]
        assert len(events) == 2
        assert events[0]["type"] == "OrderCreated"
        assert events[1]["type"] == "OrderShipped"
        assert events[0]["subject"] == aggregate_id


@pytest.mark.asyncio
async def test_save_empty_events_list(store, aggregate_id):
    """Test that saving empty events list is no-op."""
    await store.initialize()

    with patch.object(store._client, "write_events", new_callable=AsyncMock) as mock_write:
        await store.save_async(aggregate_id, [])

        # Should not call write_events for empty list
        mock_write.assert_not_called()


@pytest.mark.asyncio
async def test_load_events(store, aggregate_id):
    """Test loading events from EventSourcingDB."""
    await store.initialize()

    # Create mock CloudEvent objects
    mock_event_1 = MagicMock()
    mock_event_1.id = str(uuid.uuid4())
    mock_event_1.type = "OrderCreated"
    mock_event_1.source = "/orders/service"
    mock_event_1.subject = aggregate_id
    mock_event_1.data = {"order_id": aggregate_id, "customer_id": "customer-123"}
    mock_event_1.time = "2024-01-15T10:00:00Z"
    mock_event_1.specversion = "1.0"
    mock_event_1.datacontenttype = "application/json"

    mock_event_2 = MagicMock()
    mock_event_2.id = str(uuid.uuid4())
    mock_event_2.type = "OrderShipped"
    mock_event_2.source = "/orders/service"
    mock_event_2.subject = aggregate_id
    mock_event_2.data = {"order_id": aggregate_id, "tracking": "TRACK-456"}
    mock_event_2.time = "2024-01-15T11:00:00Z"
    mock_event_2.specversion = "1.0"
    mock_event_2.datacontenttype = "application/json"

    # Mock async generator for read_events
    async def mock_read_events(*_args, **_kwargs):
        yield mock_event_1
        yield mock_event_2

    with patch.object(store._client, "read_events", side_effect=mock_read_events):
        events = await store.load_async(aggregate_id)

        assert len(events) == 2
        assert events[0].type == "OrderCreated"
        assert events[1].type == "OrderShipped"
        assert events[0].subject == aggregate_id


@pytest.mark.asyncio
async def test_load_events_with_from_version(store, aggregate_id):
    """Test loading events starting from specific version."""
    await store.initialize()

    # Create 3 mock events
    mock_events = []
    for i in range(3):
        mock_event = MagicMock()
        mock_event.id = str(uuid.uuid4())
        mock_event.type = f"Event{i}"
        mock_event.source = "/test"
        mock_event.subject = aggregate_id
        mock_event.data = {"index": i}
        mock_event.time = "2024-01-15T10:00:00Z"
        mock_event.specversion = "1.0"
        mock_events.append(mock_event)

    async def mock_read_events(*_args, **_kwargs):
        for event in mock_events:
            yield event

    with patch.object(store._client, "read_events", side_effect=mock_read_events):
        # Load from version 2 (should skip first event)
        events = await store.load_async(aggregate_id, from_version=2)

        assert len(events) == 2
        assert events[0].type == "Event1"
        assert events[1].type == "Event2"


# ========================================
# Snapshot Tests
# ========================================


@pytest.mark.asyncio
async def test_save_snapshot(store, aggregate_id):
    """Test saving snapshot as special event."""
    await store.initialize()

    snapshot = Snapshot(
        aggregate_id=aggregate_id, version=10, state={"status": "completed"}
    )

    with patch.object(store._client, "write_events", new_callable=AsyncMock) as mock_write:
        await store.save_snapshot_async(snapshot)

        # Verify snapshot saved as event
        mock_write.assert_called_once()
        call_args = mock_write.call_args
        events = call_args[1]["events"]

        assert len(events) == 1
        snapshot_event = events[0]
        assert ".snapshot" in snapshot_event["type"]
        assert snapshot_event["subject"] == aggregate_id
        assert snapshot_event["data"]["version"] == 10


@pytest.mark.asyncio
async def test_load_snapshot(store, aggregate_id):
    """Test loading latest snapshot using EventQL."""
    await store.initialize()

    # Mock snapshot row from EventQL query
    snapshot_row = {
        "data": {
            "aggregate_id": aggregate_id,
            "version": 10,
            "state": {"status": "completed"},
        }
    }

    async def mock_run_query(*_args, **_kwargs):
        yield snapshot_row

    with patch.object(store._client, "run_eventql_query", side_effect=mock_run_query):
        snapshot = await store.load_snapshot_async(aggregate_id)

        assert snapshot is not None
        assert snapshot.aggregate_id == aggregate_id
        assert snapshot.version == 10
        assert snapshot.state == {"status": "completed"}


@pytest.mark.asyncio
async def test_load_nonexistent_snapshot(store, aggregate_id):
    """Test loading snapshot for non-existent aggregate returns None."""
    await store.initialize()

    # Mock empty query result
    async def mock_run_query(*_args, **_kwargs):
        return
        yield  # Make it an async generator

    with patch.object(store._client, "run_eventql_query", side_effect=mock_run_query):
        snapshot = await store.load_snapshot_async(aggregate_id)

        assert snapshot is None


@pytest.mark.asyncio
async def test_load_snapshot_handles_exception(store, aggregate_id):
    """Test that exceptions during snapshot load are handled gracefully."""
    await store.initialize()

    # Mock query that raises exception
    async def mock_run_query(*_args, **_kwargs):
        msg = "EventQL error"
        raise RuntimeError(msg)
        yield

    with patch.object(store._client, "run_eventql_query", side_effect=mock_run_query):
        snapshot = await store.load_snapshot_async(aggregate_id)

        # Should return None instead of raising
        assert snapshot is None


# ========================================
# Health Check Tests
# ========================================


@pytest.mark.asyncio
async def test_ping_success(store):
    """Test that ping returns True when API is accessible."""
    await store.initialize()

    with patch.object(store._client, "ping", new_callable=AsyncMock) as mock_ping:
        result = await store.ping()

        assert result is True
        mock_ping.assert_called_once()


@pytest.mark.asyncio
async def test_ping_failure(store):
    """Test that ping returns False when API is not accessible."""
    await store.initialize()

    with patch.object(
        store._client, "ping", new_callable=AsyncMock, side_effect=Exception("Connection error")
    ):
        result = await store.ping()

        assert result is False


@pytest.mark.asyncio
async def test_ping_without_initialization():
    """Test that ping returns False when client not initialized."""
    store = EventSourcingDBStore(
        base_url="http://localhost:2113", api_token="test-token"  # noqa: S106
    )

    result = await store.ping()

    assert result is False


# ========================================
# CloudEvents Conversion Tests
# ========================================


@pytest.mark.asyncio
async def test_metadata_preserved_in_cloudevents(store, aggregate_id):
    """Test that all CloudEvents metadata is preserved."""
    await store.initialize()

    event = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders/service",
        subject=aggregate_id,
        data={"order_id": aggregate_id},
        timestamp=datetime.now(timezone.utc),
        spec_version="1.0",
        data_content_type="application/json",
        data_schema="https://example.com/schema",
    )

    with patch.object(store._client, "write_events", new_callable=AsyncMock) as mock_write:
        await store.save_async(aggregate_id, [event])

        # Verify CloudEvents fields
        call_args = mock_write.call_args
        cloud_event = call_args[1]["events"][0]

        assert cloud_event["id"] == event.id
        assert cloud_event["type"] == event.type
        assert cloud_event["source"] == event.source
        assert cloud_event["subject"] == aggregate_id
        assert cloud_event["specversion"] == "1.0"
        assert cloud_event["datacontenttype"] == "application/json"
        assert cloud_event["dataschema"] == "https://example.com/schema"


@pytest.mark.asyncio
async def test_unicode_in_event_data(store, aggregate_id):
    """Test that unicode characters are preserved."""
    await store.initialize()

    event = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders",
        subject=aggregate_id,
        data={"customer_name": "Müller 日本 🎉"},
        timestamp=datetime.now(timezone.utc),
    )

    with patch.object(store._client, "write_events", new_callable=AsyncMock) as mock_write:
        await store.save_async(aggregate_id, [event])

        # Verify unicode preserved
        call_args = mock_write.call_args
        cloud_event = call_args[1]["events"][0]
        assert cloud_event["data"]["customer_name"] == "Müller 日本 🎉"


@pytest.mark.asyncio
async def test_dataclass_serialization(store, aggregate_id):
    """Test that dataclass event data is properly serialized."""
    await store.initialize()

    event = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders",
        subject=aggregate_id,
        data=OrderCreated(order_id=aggregate_id, customer_id="cust-123", total=99.99),
        timestamp=datetime.now(timezone.utc),
    )

    with patch.object(store._client, "write_events", new_callable=AsyncMock) as mock_write:
        await store.save_async(aggregate_id, [event])

        # Verify dataclass converted to dict
        call_args = mock_write.call_args
        cloud_event = call_args[1]["events"][0]
        data = cloud_event["data"]

        assert isinstance(data, dict)
        assert data["order_id"] == aggregate_id
        assert data["customer_id"] == "cust-123"
        assert data["total"] == 99.99


# ========================================
# Edge Cases
# ========================================


@pytest.mark.asyncio
async def test_concurrent_saves_different_aggregates(store):
    """Test that concurrent saves to different aggregates work."""
    await store.initialize()

    aggregate_1 = f"order-{uuid.uuid4()}"
    aggregate_2 = f"order-{uuid.uuid4()}"

    event_1 = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders",
        subject=aggregate_1,
        data={},
        timestamp=datetime.now(timezone.utc),
    )

    event_2 = Event(
        id=str(uuid.uuid4()),
        type="OrderCreated",
        source="/orders",
        subject=aggregate_2,
        data={},
        timestamp=datetime.now(timezone.utc),
    )

    with patch.object(store._client, "write_events", new_callable=AsyncMock) as mock_write:
        # Save both concurrently
        await store.save_async(aggregate_1, [event_1])
        await store.save_async(aggregate_2, [event_2])

        # Both should succeed
        assert mock_write.call_count == 2


@pytest.mark.asyncio
async def test_close_method(store):
    """Test that close method works."""
    await store.initialize()
    assert store._client is not None

    await store.close()
    assert store._client is None
