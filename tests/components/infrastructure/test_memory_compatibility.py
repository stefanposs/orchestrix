"""Tests for memory.py compatibility layer.

Tests the backward compatibility aliases in the memory module.
"""

import pytest
from dataclasses import dataclass

from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus
from orchestrix.core.message import Event, Command


@dataclass(frozen=True, kw_only=True)
class MockEvent(Event):
    """Mock event for testing."""

    value: str = "test"


@dataclass(frozen=True, kw_only=True)
class MockCommand(Command):
    """Mock command for testing."""

    value: str = "test"


class TestMemoryEventStore:
    """Test memory event store aliases."""

    @pytest.mark.asyncio
    async def test_save_async_alias(self):
        """Test save_async method works."""
        store = InMemoryEventStore()
        event = MockEvent()

        # Should work with async alias
        await store.save_async("agg-1", [event])

        # load is also async on InMemoryAsyncEventStore
        loaded = await store.load("agg-1")
        assert len(loaded) == 1

    @pytest.mark.asyncio
    async def test_load_async_alias(self):
        """Test load_async method works."""
        store = InMemoryEventStore()
        event = MockEvent()

        # save is also async
        await store.save("agg-2", [event])

        # Should work with async alias
        loaded = await store.load_async("agg-2")
        assert len(loaded) == 1

    @pytest.mark.asyncio
    async def test_snapshot_save_async(self):
        """Test save_snapshot_async works."""
        from orchestrix.core.snapshot import Snapshot
        from dataclasses import dataclass

        @dataclass
        class TestAggregate:
            pass

        store = InMemoryEventStore()
        snapshot = Snapshot(
            aggregate_id="agg-3",
            aggregate_type=TestAggregate,
            version=1,
            state={"data": "test"},
        )

        await store.save_snapshot_async(snapshot)

        loaded = await store.load_snapshot("agg-3")
        assert loaded is not None
        assert loaded.version == 1

    @pytest.mark.asyncio
    async def test_snapshot_load_async(self):
        """Test load_snapshot_async works."""
        from orchestrix.core.snapshot import Snapshot
        from dataclasses import dataclass

        @dataclass
        class TestAggregate2:
            pass

        store = InMemoryEventStore()
        snapshot = Snapshot(
            aggregate_id="agg-4",
            aggregate_type=TestAggregate2,
            version=2,
            state={"data": "snapshot"},
        )

        await store.save_snapshot(snapshot)

        loaded = await store.load_snapshot_async("agg-4")
        assert loaded is not None
        assert loaded.version == 2


class TestMemoryMessageBus:
    """Test memory message bus aliases."""

    @pytest.mark.asyncio
    async def test_publish_async_alias(self):
        """Test publish_async method works."""
        bus = InMemoryMessageBus()
        message = MockCommand()

        # Register a handler to catch the message
        called = []

        async def handler(msg):
            called.append(msg)

        bus.subscribe(MockCommand, handler)

        # Should work with async alias
        await bus.publish_async(message)

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_subscribe_still_works(self):
        """Test subscribe method still works."""
        bus = InMemoryMessageBus()
        message = MockCommand()

        received = []

        async def handler(msg):
            received.append(msg)

        bus.subscribe(MockCommand, handler)

        await bus.publish_async(message)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Test multiple subscribers work."""
        bus = InMemoryMessageBus()
        message = MockEvent()

        calls_1 = []
        calls_2 = []

        async def handler1(msg):
            calls_1.append(msg)

        async def handler2(msg):
            calls_2.append(msg)

        bus.subscribe(MockEvent, handler1)
        bus.subscribe(MockEvent, handler2)

        await bus.publish_async(message)

        assert len(calls_1) == 1
        assert len(calls_2) == 1


class TestMemoryCompatibility:
    """Test that memory.py provides proper compatibility."""

    def test_store_is_async_store_subclass(self):
        """Test InMemoryEventStore is InMemoryAsyncEventStore."""
        from orchestrix.infrastructure.async_inmemory_store import InMemoryAsyncEventStore

        store = InMemoryEventStore()
        assert isinstance(store, InMemoryAsyncEventStore)

    def test_bus_is_async_bus_subclass(self):
        """Test InMemoryMessageBus is InMemoryAsyncMessageBus."""
        from orchestrix.infrastructure.async_inmemory_bus import InMemoryAsyncMessageBus

        bus = InMemoryMessageBus()
        assert isinstance(bus, InMemoryAsyncMessageBus)

    def test_exports_are_available(self):
        """Test __all__ exports are correct."""
        from orchestrix.infrastructure import memory

        assert hasattr(memory, "InMemoryEventStore")
        assert hasattr(memory, "InMemoryMessageBus")
        assert "InMemoryEventStore" in memory.__all__
        assert "InMemoryMessageBus" in memory.__all__
