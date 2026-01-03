"""Edge case and error scenario tests.

Tests for boundary conditions, concurrent access, empty states,
and other edge cases that could occur in production.
"""

import asyncio
from dataclasses import dataclass

import pytest

from orchestrix.core.dead_letter_queue import DeadLetteredMessage, InMemoryDeadLetterQueue
from orchestrix.core.exceptions import HandlerError
from orchestrix.infrastructure import InMemoryEventStore, InMemoryMessageBus
from orchestrix.infrastructure.async_inmemory_bus import InMemoryAsyncMessageBus
from orchestrix.infrastructure.async_inmemory_store import InMemoryAsyncEventStore
from orchestrix.core.message import Command, Event
from orchestrix.core.snapshot import Snapshot


@dataclass(frozen=True)
class TestCommand(Command):
    """Test command."""

    value: str = "test"


@dataclass(frozen=True)
class TestEvent(Event):
    """Test event."""

    value: str = "test"


class TestEmptyStates:
    """Test behavior with empty/initial states."""

    def test_event_store_load_empty_aggregate(self) -> None:
        """Loading non-existent aggregate returns empty list."""
        store = InMemoryEventStore()
        events = store.load("nonexistent-id")

        assert events == []
        assert len(events) == 0

    def test_event_store_save_empty_list(self) -> None:
        """Saving empty event list should work."""
        store = InMemoryEventStore()
        store.save("agg-123", [])

        events = store.load("agg-123")
        assert events == []

    def test_message_bus_publish_without_subscribers(self) -> None:
        """Publishing without subscribers should not raise."""
        bus = InMemoryMessageBus()
        cmd = TestCommand()

        # Should not raise
        bus.publish(cmd)

    def test_message_bus_subscribe_then_unsubscribe(self) -> None:
        """After unsubscribe, handler should not be called."""
        bus = InMemoryMessageBus()
        calls = []

        def handler(msg: TestCommand) -> None:
            calls.append(msg)

        bus.subscribe(TestCommand, handler)
        bus.publish(TestCommand())
        assert len(calls) == 1

        # Unsubscribe by clearing handlers (no explicit API)
        # Bus should handle no handlers gracefully
        bus._handlers[TestCommand].clear()
        bus.publish(TestCommand())
        assert len(calls) == 1  # No new call

    def test_dlq_empty_queue_operations(self) -> None:
        """DLQ operations on empty queue."""
        dlq = InMemoryDeadLetterQueue()

        assert dlq.count() == 0
        assert dlq.dequeue_all() == []
        assert dlq.get_by_message_id("nonexistent") is None
        assert dlq.get_by_reason("any") == []

        # Clear on empty should not raise
        dlq.clear()


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    def test_event_store_very_long_aggregate_id(self) -> None:
        """Event store with very long aggregate ID."""
        store = InMemoryEventStore()
        long_id = "a" * 1000

        events = [TestEvent(), TestEvent()]
        store.save(long_id, events)

        loaded = store.load(long_id)
        assert len(loaded) == 2

    def test_event_store_many_aggregates(self) -> None:
        """Event store with many aggregates."""
        store = InMemoryEventStore()

        # Create 1000 aggregates
        for i in range(1000):
            store.save(f"agg-{i}", [TestEvent()])

        # All should be isolated
        for i in range(1000):
            events = store.load(f"agg-{i}")
            assert len(events) == 1

    def test_message_bus_many_handlers(self) -> None:
        """Message bus with many handlers for same type."""
        bus = InMemoryMessageBus()
        calls = []

        # Subscribe 100 handlers
        for i in range(100):

            def handler(_msg: TestCommand, idx: int = i) -> None:
                calls.append(idx)

            bus.subscribe(TestCommand, handler)

        bus.publish(TestCommand())

        assert len(calls) == 100
        assert set(calls) == set(range(100))

    def test_snapshot_at_zero_version(self) -> None:
        """Snapshot at version 0 (boundary)."""
        store = InMemoryEventStore()
        snapshot = Snapshot(
            aggregate_id="agg-001",
            aggregate_type="Test",
            version=0,
            state={},
        )

        store.save_snapshot(snapshot)
        loaded = store.load_snapshot("agg-001")

        assert loaded is not None
        assert loaded.version == 0

    def test_load_events_from_future_version(self) -> None:
        """Loading from version beyond stream length."""
        store = InMemoryEventStore()
        store.save("agg-001", [TestEvent(), TestEvent(), TestEvent()])

        # Load from version 10 (only 3 events)
        events = store.load("agg-001", from_version=10)

        assert events == []


class TestConcurrentAccess:
    """Test concurrent access patterns."""

    @pytest.mark.asyncio
    async def test_async_bus_concurrent_publishes(self) -> None:
        """Multiple concurrent publishes to async bus."""
        bus = InMemoryAsyncMessageBus()
        received = []

        async def handler(msg: TestCommand) -> None:
            await asyncio.sleep(0.01)  # Simulate work
            received.append(msg.value)

        bus.subscribe(TestCommand, handler)

        # Publish 10 commands concurrently
        commands = [TestCommand(value=f"cmd-{i}") for i in range(10)]
        await asyncio.gather(*[bus.publish(cmd) for cmd in commands])

        assert len(received) == 10
        assert set(received) == {f"cmd-{i}" for i in range(10)}

    @pytest.mark.asyncio
    async def test_async_store_concurrent_saves(self) -> None:
        """Concurrent saves to different aggregates."""
        store = InMemoryAsyncEventStore()

        async def save_events(agg_id: str) -> None:
            events = [TestEvent(value=f"event-{agg_id}")]
            await store.save(agg_id, events)

        # Save to 50 aggregates concurrently
        await asyncio.gather(*[save_events(f"agg-{i}") for i in range(50)])

        # All should be saved
        for i in range(50):
            events = await store.load(f"agg-{i}")
            assert len(events) == 1
            assert events[0].value == f"event-agg-{i}"

    @pytest.mark.asyncio
    async def test_async_store_concurrent_reads(self) -> None:
        """Concurrent reads from same aggregate."""
        store = InMemoryAsyncEventStore()
        events = [TestEvent() for _ in range(5)]
        await store.save("agg-001", events)

        # Read 20 times concurrently
        results = await asyncio.gather(*[store.load("agg-001") for _ in range(20)])

        # All reads should return same data
        for result in results:
            assert len(result) == 5


class TestInvalidInputs:
    """Test handling of invalid inputs."""

    def test_message_bus_handler_with_wrong_signature(self) -> None:
        """Handler with wrong signature raises HandlerError."""
        bus = InMemoryMessageBus()

        def bad_handler() -> None:  # Missing message parameter
            pass

        bus.subscribe(TestCommand, bad_handler)  # type: ignore

        # Should raise HandlerError when all handlers fail
        with pytest.raises(HandlerError):
            bus.publish(TestCommand())

    def test_event_store_load_with_negative_version(self) -> None:
        """Load with negative version (boundary)."""
        store = InMemoryEventStore()
        store.save("agg-001", [TestEvent(), TestEvent()])

        # Negative version - implementation may vary
        # Current implementation uses list slicing which handles this
        events = store.load("agg-001", from_version=-1)

        # Should get last event
        assert len(events) == 1

    def test_dlq_duplicate_message_ids(self) -> None:
        """DLQ can handle multiple messages with same ID."""
        dlq = InMemoryDeadLetterQueue()
        msg = TestCommand(value="test")

        # Add same message ID twice with different reasons
        dlq.enqueue(
            DeadLetteredMessage(message=msg, reason="Error 1", failure_count=1)
        )
        dlq.enqueue(
            DeadLetteredMessage(message=msg, reason="Error 2", failure_count=2)
        )

        assert dlq.count() == 2

        # get_by_message_id returns first match
        found = dlq.get_by_message_id(msg.id)
        assert found is not None
        assert found.reason == "Error 1"


class TestErrorRecovery:
    """Test error recovery scenarios."""

    def test_message_bus_all_handlers_fail_but_continue(self) -> None:
        """All handlers fail - should raise HandlerError."""
        bus = InMemoryMessageBus()

        def failing_handler1(_msg: TestCommand) -> None:
            msg = "Handler 1 failed"
            raise ValueError(msg)

        def failing_handler2(_msg: TestCommand) -> None:
            msg = "Handler 2 failed"
            raise RuntimeError(msg)

        bus.subscribe(TestCommand, failing_handler1)
        bus.subscribe(TestCommand, failing_handler2)

        with pytest.raises(HandlerError) as exc_info:
            bus.publish(TestCommand())

        # HandlerError message indicates all handlers failed
        assert "all_handlers" in str(exc_info.value)
        assert "2 handlers failed" in str(exc_info.value)

    def test_message_bus_some_handlers_succeed(self) -> None:
        """Some handlers fail, others succeed - should not raise."""
        bus = InMemoryMessageBus()
        success_calls = []

        def failing_handler(_msg: TestCommand) -> None:
            msg = "Failed"
            raise ValueError(msg)

        def success_handler(msg: TestCommand) -> None:
            success_calls.append(msg)

        bus.subscribe(TestCommand, failing_handler)
        bus.subscribe(TestCommand, success_handler)
        bus.subscribe(TestCommand, failing_handler)

        # Should not raise (at least one handler succeeded)
        bus.publish(TestCommand())

        assert len(success_calls) == 1

    @pytest.mark.asyncio
    async def test_async_bus_partial_handler_failures(self) -> None:
        """Async bus with mix of successful and failing handlers."""
        bus = InMemoryAsyncMessageBus()
        successes = []

        async def failing_handler(_msg: TestCommand) -> None:
            msg = "Async fail"
            raise ValueError(msg)

        async def success_handler(msg: TestCommand) -> None:
            successes.append(msg.value)

        bus.subscribe(TestCommand, failing_handler)
        bus.subscribe(TestCommand, success_handler)
        bus.subscribe(TestCommand, failing_handler)

        # Should not raise (one success)
        await bus.publish(TestCommand(value="test-1"))

        assert len(successes) == 1


class TestSnapshotEdgeCases:
    """Test snapshot edge cases."""

    def test_snapshot_very_large_state(self) -> None:
        """Snapshot with large state dictionary."""
        store = InMemoryEventStore()
        large_state = {f"key-{i}": f"value-{i}" for i in range(10000)}

        snapshot = Snapshot(
            aggregate_id="agg-001",
            aggregate_type="Large",
            version=100,
            state=large_state,
        )

        store.save_snapshot(snapshot)
        loaded = store.load_snapshot("agg-001")

        assert loaded is not None
        assert len(loaded.state) == 10000

    def test_snapshot_empty_state(self) -> None:
        """Snapshot with empty state dictionary."""
        store = InMemoryEventStore()
        snapshot = Snapshot(
            aggregate_id="agg-001",
            aggregate_type="Empty",
            version=0,
            state={},
        )

        store.save_snapshot(snapshot)
        loaded = store.load_snapshot("agg-001")

        assert loaded is not None
        assert loaded.state == {}

    @pytest.mark.asyncio
    async def test_async_snapshot_operations(self) -> None:
        """Async snapshot save and load."""
        store = InMemoryAsyncEventStore()
        snapshot = Snapshot(
            aggregate_id="agg-001",
            aggregate_type="Async",
            version=50,
            state={"test": "data"},
        )

        await store.save_snapshot(snapshot)
        loaded = await store.load_snapshot("agg-001")

        assert loaded is not None
        assert loaded.version == 50
        assert loaded.state == {"test": "data"}


class TestMessageImmutability:
    """Test that messages remain immutable even in edge cases."""

    def test_cannot_modify_message_after_creation(self) -> None:
        """Messages are frozen and cannot be modified."""
        cmd = TestCommand(value="original")

        with pytest.raises(AttributeError):
            cmd.value = "modified"  # type: ignore

    def test_message_in_dlq_cannot_be_modified(self) -> None:
        """Messages in DLQ remain immutable."""
        dlq = InMemoryDeadLetterQueue()
        msg = TestCommand(value="test")

        dead_lettered = DeadLetteredMessage(
            message=msg, reason="Failed", failure_count=1
        )
        dlq.enqueue(dead_lettered)

        # Cannot modify the dead lettered message
        with pytest.raises(AttributeError):
            dead_lettered.reason = "New reason"  # type: ignore

    def test_events_in_store_cannot_be_modified(self) -> None:
        """Events in store remain immutable."""
        store = InMemoryEventStore()
        event = TestEvent(value="original")

        store.save("agg-001", [event])
        loaded = store.load("agg-001")

        # Cannot modify loaded event
        with pytest.raises(AttributeError):
            loaded[0].value = "modified"  # type: ignore
