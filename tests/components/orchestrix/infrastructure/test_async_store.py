"""Tests for async event store."""

import pytest
from orchestrix.core.messaging.message import Event
from orchestrix.infrastructure.memory.async_store import InMemoryAsyncEventStore


@pytest.fixture
def async_store():
    """Provide a fresh InMemoryAsyncEventStore for each test."""
    return InMemoryAsyncEventStore()


class UserCreated(Event):
    """Test event."""

    user_id: str = "user-123"


class UserUpdated(Event):
    """Test event."""

    user_id: str = "user-123"


class TestAsyncEventStore:
    """Test async event store."""

    @pytest.mark.asyncio
    async def test_save_and_load_events(self, async_store):
        """Test saving and loading events."""
        aggregate_id = "agg-001"
        events = [UserCreated(), UserUpdated()]

        await async_store.save(aggregate_id, events)
        loaded = await async_store.load(aggregate_id)

        assert len(loaded) == 2
        assert loaded[0].type == "UserCreated"
        assert loaded[1].type == "UserUpdated"

    @pytest.mark.asyncio
    async def test_load_nonexistent_aggregate(self, async_store):
        """Test loading events for non-existent aggregate."""
        loaded = await async_store.load("nonexistent")

        assert loaded == []

    @pytest.mark.asyncio
    async def test_save_multiple_times(self, async_store):
        """Test saving events multiple times to same aggregate."""
        aggregate_id = "agg-002"

        # First save
        await async_store.save(aggregate_id, [UserCreated()])
        # Second save
        await async_store.save(aggregate_id, [UserUpdated()])

        loaded = await async_store.load(aggregate_id)

        assert len(loaded) == 2
        assert loaded[0].type == "UserCreated"
        assert loaded[1].type == "UserUpdated"

    @pytest.mark.asyncio
    async def test_different_aggregates_isolated(self, async_store):
        """Test that different aggregates are isolated."""
        agg1_id = "agg-001"
        agg2_id = "agg-002"

        await async_store.save(agg1_id, [UserCreated()])
        await async_store.save(agg2_id, [UserUpdated()])

        loaded1 = await async_store.load(agg1_id)
        loaded2 = await async_store.load(agg2_id)

        assert len(loaded1) == 1
        assert loaded1[0].type == "UserCreated"
        assert len(loaded2) == 1
        assert loaded2[0].type == "UserUpdated"

    @pytest.mark.asyncio
    async def test_save_empty_list(self, async_store):
        """Test saving empty event list."""
        aggregate_id = "agg-003"

        await async_store.save(aggregate_id, [])
        loaded = await async_store.load(aggregate_id)

        assert loaded == []

    @pytest.mark.asyncio
    async def test_load_from_version(self, async_store):
        """Test loading events from specific version."""
        aggregate_id = "agg-004"

        # Save 3 events
        event1 = UserCreated()
        event2 = UserUpdated()
        event3 = UserCreated()
        await async_store.save(aggregate_id, [event1, event2, event3])

        # Load from version 1 (skip first event)
        loaded = await async_store.load(aggregate_id, from_version=1)

        assert len(loaded) == 2
        assert loaded[0] == event2
        assert loaded[1] == event3

    @pytest.mark.asyncio
    async def test_load_from_version_beyond_length(self, async_store):
        """Test loading from version beyond event count."""
        aggregate_id = "agg-005"

        await async_store.save(aggregate_id, [UserCreated(), UserUpdated()])

        # Load from version 10 (beyond the 2 events)
        loaded = await async_store.load(aggregate_id, from_version=10)

        assert loaded == []

    @pytest.mark.asyncio
    async def test_concurrent_saves_different_aggregates(self, async_store):
        """Test concurrent saves to different aggregates."""
        import asyncio

        async def save_aggregate(agg_id: str) -> None:
            await async_store.save(agg_id, [UserCreated(), UserUpdated()])

        # Save to multiple aggregates concurrently
        await asyncio.gather(
            save_aggregate("agg-a"),
            save_aggregate("agg-b"),
            save_aggregate("agg-c"),
        )

        # Verify all aggregates saved correctly
        agg_a = await async_store.load("agg-a")
        agg_b = await async_store.load("agg-b")
        agg_c = await async_store.load("agg-c")

        assert len(agg_a) == 2
        assert len(agg_b) == 2
        assert len(agg_c) == 2

    @pytest.mark.asyncio
    async def test_event_ordering_preserved(self, async_store):
        """Test that event ordering is preserved."""
        aggregate_id = "agg-006"

        events = [
            UserCreated(),
            UserUpdated(),
            UserCreated(),
            UserUpdated(),
        ]

        await async_store.save(aggregate_id, events)
        loaded = await async_store.load(aggregate_id)

        # Verify order is preserved
        assert [e.type for e in loaded] == [
            "UserCreated",
            "UserUpdated",
            "UserCreated",
            "UserUpdated",
        ]

    @pytest.mark.asyncio
    async def test_large_event_stream(self, async_store):
        """Test storing and loading large event streams."""
        aggregate_id = "agg-large"

        # Create 1000 events
        events = [UserCreated() if i % 2 == 0 else UserUpdated() for i in range(1000)]

        await async_store.save(aggregate_id, events)
        loaded = await async_store.load(aggregate_id)

        assert len(loaded) == 1000
        # Verify alternating pattern preserved
        for i, event in enumerate(loaded):
            expected_type = "UserCreated" if i % 2 == 0 else "UserUpdated"
            assert event.type == expected_type
