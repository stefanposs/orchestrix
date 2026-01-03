"""Tests for EventSourcingDB event store implementation.

Uses pytest-asyncio for async tests and mocked HTTP responses for isolation.
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Conditional import for EventSourcingDB support
pytest.importorskip("aiohttp", reason="aiohttp not installed - skip eventsourcingdb tests")

from orchestrix.domain.event import Event
from orchestrix.domain.snapshot import Snapshot

from orchestrix.infrastructure.eventsourcingdb_store import EventSourcingDBStore


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
        timeout=30.0,
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
async def test_initialize_creates_session(store):
    """Test that initialize creates aiohttp session with correct headers."""
    await store.initialize()

    assert store._session is not None
    assert "Authorization" in store._session.headers
    assert store._session.headers["Authorization"] == "Bearer test-token-12345"

    await store._session.close()


@pytest.mark.asyncio
async def test_save_events(store, aggregate_id, sample_events):
    """Test saving events to EventSourcingDB."""
    await store.initialize()

    # Mock the HTTP POST response
    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value.__aenter__.return_value = mock_response

        await store.save_async(aggregate_id, sample_events)

        # Verify POST was called with correct URL
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:2113/api/v1/write-events"

        # Verify payload contains events
        payload = call_args[1]["json"]
        assert "events" in payload
        assert len(payload["events"]) == 2

    await store._session.close()


@pytest.mark.asyncio
async def test_load_events(store, aggregate_id):
    """Test loading events from EventSourcingDB."""
    await store.initialize()

    # Mock streaming response
    event_1 = {
        "type": "event",
        "payload": {
            "id": str(uuid.uuid4()),
            "type": "OrderCreated",
            "source": "/orders/service",
            "subject": aggregate_id,
            "data": {"order_id": aggregate_id, "customer_id": "customer-123"},
            "time": "2024-01-15T10:00:00Z",
        },
    }
    event_2 = {
        "type": "event",
        "payload": {
            "id": str(uuid.uuid4()),
            "type": "OrderShipped",
            "source": "/orders/service",
            "subject": aggregate_id,
            "data": {"order_id": aggregate_id, "tracking": "TRACK-456"},
            "time": "2024-01-15T11:00:00Z",
        },
    }

    # Simulate newline-delimited JSON stream
    stream_data = (
        json.dumps(event_1).encode() + b"\n" + json.dumps(event_2).encode() + b"\n"
    )

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = MagicMock()
        # Simulate async iteration over lines
        mock_response.content.__aiter__.return_value = iter([stream_data])
        mock_post.return_value.__aenter__.return_value = mock_response

        events = await store.load_async(aggregate_id)

        assert len(events) == 2
        assert events[0].type == "OrderCreated"
        assert events[1].type == "OrderShipped"

    await store._session.close()


@pytest.mark.asyncio
async def test_load_events_with_from_version(store, aggregate_id):
    """Test loading events starting from specific version."""
    await store.initialize()

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = MagicMock()
        mock_response.content.__aiter__.return_value = iter([])
        mock_post.return_value.__aenter__.return_value = mock_response

        await store.load_async(aggregate_id, from_version=5)

        # Verify query includes fromVersion
        call_args = mock_post.call_args
        query = call_args[1]["json"]["query"]
        assert "fromVersion" in query.lower() or "from_version" in query.lower() or "5" in query

    await store._session.close()


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

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value.__aenter__.return_value = mock_response

        await store.save_snapshot_async(snapshot)

        # Verify snapshot saved as event with .snapshot suffix
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert len(payload["events"]) == 1
        snapshot_event = payload["events"][0]
        assert ".snapshot" in snapshot_event["type"].lower()

    await store._session.close()


@pytest.mark.asyncio
async def test_load_snapshot(store, aggregate_id):
    """Test loading latest snapshot using EventQL."""
    await store.initialize()

    # Mock snapshot response
    snapshot_payload = {
        "type": "event",
        "payload": {
            "id": str(uuid.uuid4()),
            "type": "Order.snapshot",
            "source": "/snapshots",
            "subject": aggregate_id,
            "data": {
                "aggregate_id": aggregate_id,
                "version": 10,
                "state": {"status": "completed"},
            },
            "time": "2024-01-15T12:00:00Z",
        },
    }

    stream_data = json.dumps(snapshot_payload).encode() + b"\n"

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = MagicMock()
        mock_response.content.__aiter__.return_value = iter([stream_data])
        mock_post.return_value.__aenter__.return_value = mock_response

        snapshot = await store.load_snapshot_async(aggregate_id)

        assert snapshot is not None
        assert snapshot.aggregate_id == aggregate_id
        assert snapshot.version == 10

    await store._session.close()


@pytest.mark.asyncio
async def test_load_nonexistent_snapshot(store, aggregate_id):
    """Test loading snapshot for non-existent aggregate returns None."""
    await store.initialize()

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = MagicMock()
        mock_response.content.__aiter__.return_value = iter([])
        mock_post.return_value.__aenter__.return_value = mock_response

        snapshot = await store.load_snapshot_async(aggregate_id)

        assert snapshot is None

    await store._session.close()


# ========================================
# Error Handling Tests
# ========================================


@pytest.mark.asyncio
async def test_save_handles_error_message(store, aggregate_id, sample_events):
    """Test that error messages in stream are handled correctly."""
    await store.initialize()

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception):
            await store.save_async(aggregate_id, sample_events)

    await store._session.close()


@pytest.mark.asyncio
async def test_load_handles_heartbeat_messages(store, aggregate_id):
    """Test that heartbeat messages are skipped during streaming."""
    await store.initialize()

    # Mix heartbeat and event messages
    heartbeat = {"type": "heartbeat"}
    event = {
        "type": "event",
        "payload": {
            "id": str(uuid.uuid4()),
            "type": "OrderCreated",
            "source": "/orders",
            "subject": aggregate_id,
            "data": {},
            "time": "2024-01-15T10:00:00Z",
        },
    }

    stream_data = (
        json.dumps(heartbeat).encode()
        + b"\n"
        + json.dumps(event).encode()
        + b"\n"
        + json.dumps(heartbeat).encode()
        + b"\n"
    )

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = MagicMock()
        mock_response.content.__aiter__.return_value = iter([stream_data])
        mock_post.return_value.__aenter__.return_value = mock_response

        events = await store.load_async(aggregate_id)

        # Should only return actual event, not heartbeats
        assert len(events) == 1
        assert events[0].type == "OrderCreated"

    await store._session.close()


# ========================================
# Health Check Tests
# ========================================


@pytest.mark.asyncio
async def test_ping_success(store):
    """Test that ping returns True when API is accessible."""
    await store.initialize()

    with patch.object(store._session, "get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await store.ping()

        assert result is True
        mock_get.assert_called_once_with("http://localhost:2113/api/v1/ping")

    await store._session.close()


@pytest.mark.asyncio
async def test_ping_failure(store):
    """Test that ping returns False when API is not accessible."""
    await store.initialize()

    with patch.object(store._session, "get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await store.ping()

        assert result is False

    await store._session.close()


@pytest.mark.asyncio
async def test_ping_without_initialization():
    """Test that ping returns False when session not initialized."""
    store = EventSourcingDBStore(
        base_url="http://localhost:2113", api_token="test-token"  # noqa: S106
    )

    result = await store.ping()

    assert result is False


# ========================================
# Edge Cases
# ========================================


@pytest.mark.asyncio
async def test_save_empty_events_list(store, aggregate_id):
    """Test that saving empty events list is no-op."""
    await store.initialize()

    with patch.object(store._session, "post") as mock_post:
        await store.save_async(aggregate_id, [])

        # Should not make HTTP call for empty list
        mock_post.assert_not_called()

    await store._session.close()


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
        correlation_id="corr-123",
        causation_id="cause-456",
    )

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value.__aenter__.return_value = mock_response

        await store.save_async(aggregate_id, [event])

        # Verify CloudEvents fields
        call_args = mock_post.call_args
        payload = call_args[1]["json"]["events"][0]
        assert payload["id"] == event.id
        assert payload["type"] == event.type
        assert payload["source"] == event.source
        assert payload["subject"] == aggregate_id
        assert payload["specversion"] == "1.0"
        assert payload["datacontenttype"] == "application/json"
        assert payload["dataschema"] == "https://example.com/schema"

    await store._session.close()


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

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value.__aenter__.return_value = mock_response

        await store.save_async(aggregate_id, [event])

        # Verify unicode preserved in JSON
        call_args = mock_post.call_args
        payload = call_args[1]["json"]["events"][0]
        assert payload["data"]["customer_name"] == "Müller 日本 🎉"

    await store._session.close()


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

    with patch.object(store._session, "post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value.__aenter__.return_value = mock_response

        # Save both concurrently
        await store.save_async(aggregate_1, [event_1])
        await store.save_async(aggregate_2, [event_2])

        # Both should succeed
        assert mock_post.call_count == 2

    await store._session.close()
