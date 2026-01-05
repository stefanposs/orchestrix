"""Tests for EventSourcingDB event store implementation.

Uses pytest-asyncio for async tests with FakeEventSourcingDBClient.
This eliminates the need for mocking SDK internals.

For integration tests with real EventSourcingDB, use testcontainers.
"""

import uuid
from datetime import UTC, datetime

import pytest

# Conditional import for EventSourcingDB support
pytest.importorskip("eventsourcingdb", reason="eventsourcingdb not installed - skip tests")

from orchestrix.core.messaging.message import Event
from orchestrix.infrastructure.eventsourcingdb.store import EventSourcingDBStore


@pytest.fixture
def store(fake_esdb_client):
    """Create EventSourcingDB store with fake client."""
    store_instance = EventSourcingDBStore(
        base_url="http://localhost:2113",
        api_token="test-token-12345",  # noqa: S106
    )
    # Inject fake client instead of real one
    object.__setattr__(store_instance, "_client", fake_esdb_client)
    return store_instance


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
            source="/order",
            subject=aggregate_id,
            datacontenttype="application/json",
        ),
        Event(
            id=str(uuid.uuid4()),
            type="OrderShipped",
            source="/order",
            subject=aggregate_id,
            datacontenttype="application/json",
        ),
    ]


# Tests


@pytest.mark.asyncio
async def test_save_and_load_events(store, aggregate_id, sample_events):
    """Test saving and loading events (real behavior, no mocks)."""
    # Save events
    await store.save(aggregate_id, sample_events)

    # Load events back
    loaded_events = await store.load(aggregate_id)

    # Verify events match
    assert len(loaded_events) == 2
    assert loaded_events[0].type == "OrderCreated"
    assert loaded_events[1].type == "OrderShipped"
    assert loaded_events[0].subject == aggregate_id
    assert loaded_events[1].subject == aggregate_id


@pytest.mark.asyncio
async def test_save_empty_list(store, aggregate_id):
    """Test that saving empty list is no-op."""
    # This should not raise
    await store.save(aggregate_id, [])

    # Trying to load should fail (not found)
    with pytest.raises(ValueError):
        await store.load(aggregate_id)


@pytest.mark.asyncio
async def test_load_nonexistent_aggregate(store):
    """Test that loading non-existent aggregate raises ValueError."""
    nonexistent_id = f"order-{uuid.uuid4()}"

    with pytest.raises(ValueError, match="not found"):
        await store.load(nonexistent_id)


@pytest.mark.asyncio
async def test_multiple_aggregates(store):
    """Test loading different aggregates independently."""
    agg_id_1 = f"order-{uuid.uuid4()}"
    agg_id_2 = f"order-{uuid.uuid4()}"

    events_1 = [
        Event(
            id=str(uuid.uuid4()),
            type="OrderCreated",
            source="/order",
            subject=agg_id_1,
        ),
    ]

    events_2 = [
        Event(
            id=str(uuid.uuid4()),
            type="CustomerCreated",
            source="/customer",
            subject=agg_id_2,
        ),
    ]

    await store.save(agg_id_1, events_1)
    await store.save(agg_id_2, events_2)

    # Load separately
    loaded_1 = await store.load(agg_id_1)
    loaded_2 = await store.load(agg_id_2)

    assert loaded_1[0].type == "OrderCreated"
    assert loaded_2[0].type == "CustomerCreated"


@pytest.mark.asyncio
async def test_event_metadata_preserved(store, aggregate_id):
    """Test that all event metadata is preserved."""
    now = datetime.now(UTC)
    event_id = str(uuid.uuid4())

    event = Event(
        id=event_id,
        type="TestEvent",
        source="/test/service",
        subject=aggregate_id,
        timestamp=now,
        datacontenttype="application/json",
        dataschema="https://example.com/schema",
    )

    await store.save(aggregate_id, [event])
    loaded = await store.load(aggregate_id)

    assert loaded[0].id == event_id
    assert loaded[0].type == "TestEvent"
    assert loaded[0].source == "/test/service"
    assert loaded[0].subject == aggregate_id
    assert loaded[0].datacontenttype == "application/json"
