"""Tests for CQRS projection engine."""

import asyncio
from dataclasses import dataclass
from typing import Optional

import pytest

from orchestrix.core.message import Event
from orchestrix.core.projection import (
    InMemoryProjectionStateStore,
    ProjectionEngine,
    ProjectionState,
)


@dataclass(frozen=True)
class OrderCreated(Event):
    """Test event: order was created."""

    order_id: str
    customer_id: str
    amount: float


@dataclass(frozen=True)
class OrderShipped(Event):
    """Test event: order was shipped."""

    order_id: str


@dataclass(frozen=True)
class OrderCancelled(Event):
    """Test event: order was cancelled."""

    order_id: str
    reason: str


class TestProjectionEngine:
    """Tests for ProjectionEngine."""

    @pytest.fixture
    def state_store(self):
        """Create an in-memory state store."""
        return InMemoryProjectionStateStore()

    @pytest.fixture
    def engine(self, state_store):
        """Create a projection engine."""
        return ProjectionEngine("test-projection", state_store)

    @pytest.mark.asyncio
    async def test_initialization(self, engine, state_store):
        """Test projection engine initialization."""
        await engine.initialize()

        state = engine.get_state()
        assert state is not None
        assert state.projection_id == "test-projection"
        assert state.last_processed_event_id is None
        assert state.last_processed_position == 0
        assert state.error_count == 0
        assert state.is_healthy is True

    @pytest.mark.asyncio
    async def test_register_handler_with_decorator(self, engine, state_store):
        """Test registering handlers with decorator syntax."""
        await engine.initialize()

        call_log: list[OrderCreated] = []

        @engine.on(OrderCreated)
        async def handle_order_created(event: OrderCreated) -> None:
            call_log.append(event)

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )
        await engine.handle_event(event)

        assert len(call_log) == 1
        assert call_log[0].order_id == "order-1"

    @pytest.mark.asyncio
    async def test_sync_handler(self, engine, state_store):
        """Test handling with sync handler."""
        await engine.initialize()

        call_log: list[OrderCreated] = []

        @engine.on(OrderCreated)
        def handle_order_created(event: OrderCreated) -> None:
            call_log.append(event)

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )
        await engine.handle_event(event)

        assert len(call_log) == 1

    @pytest.mark.asyncio
    async def test_multiple_handlers_for_same_event(self, engine, state_store):
        """Test multiple handlers for the same event type."""
        await engine.initialize()

        call_log1: list[OrderCreated] = []
        call_log2: list[OrderCreated] = []

        @engine.on(OrderCreated)
        async def handler1(event: OrderCreated) -> None:
            call_log1.append(event)

        @engine.on(OrderCreated)
        async def handler2(event: OrderCreated) -> None:
            call_log2.append(event)

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )
        await engine.handle_event(event)

        assert len(call_log1) == 1
        assert len(call_log2) == 1

    @pytest.mark.asyncio
    async def test_idempotency(self, engine, state_store):
        """Test that processing the same event twice is idempotent."""
        await engine.initialize()

        call_log: list[OrderCreated] = []

        @engine.on(OrderCreated)
        async def handle_order_created(event: OrderCreated) -> None:
            call_log.append(event)

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )

        # Process same event twice
        await engine.handle_event(event)
        await engine.handle_event(event)

        # Handler should only be called once
        assert len(call_log) == 1

    @pytest.mark.asyncio
    async def test_state_persistence(self, engine, state_store):
        """Test that projection state is persisted."""
        await engine.initialize()

        @engine.on(OrderCreated)
        async def handle_order_created(event: OrderCreated) -> None:
            pass

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )
        await engine.handle_event(event)

        # Verify state was saved
        saved_state = await state_store.load_state("test-projection")
        assert saved_state is not None
        assert saved_state.last_processed_event_id == event.id

    @pytest.mark.asyncio
    async def test_process_events_stream(self, engine, state_store):
        """Test processing a stream of events."""
        await engine.initialize()

        call_log: list[Event] = []

        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            call_log.append(event)

        @engine.on(OrderShipped)
        async def handle_shipped(event: OrderShipped) -> None:
            call_log.append(event)

        events = [
            OrderCreated(order_id="order-1", customer_id="customer-1", amount=100.0),
            OrderCreated(order_id="order-2", customer_id="customer-1", amount=200.0),
            OrderShipped(order_id="order-1"),
        ]

        await engine.process_events(events)

        assert len(call_log) == 3

    @pytest.mark.asyncio
    async def test_replay_functionality(self, engine, state_store):
        """Test replaying events to rebuild read models."""
        await engine.initialize()

        call_log: list[Event] = []

        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            call_log.append(event)

        # Process events
        event1 = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )
        await engine.handle_event(event1)
        assert len(call_log) == 1

        # Replay should reset and reprocess
        call_log.clear()
        await engine.replay([event1])
        assert len(call_log) == 1

        # Verify state was reset
        state = engine.get_state()
        assert state is not None
        assert state.error_count == 0
        assert state.is_healthy is True

    @pytest.mark.asyncio
    async def test_error_handling(self, engine, state_store):
        """Test error handling in handlers."""
        await engine.initialize()

        @engine.on(OrderCreated)
        async def handle_order_created(event: OrderCreated) -> None:
            raise ValueError("Test error")

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )

        with pytest.raises(ValueError, match="Test error"):
            await engine.handle_event(event)

        # Verify error was recorded in state
        state = engine.get_state()
        assert state is not None
        assert state.error_count == 1
        assert state.is_healthy is False

    @pytest.mark.asyncio
    async def test_handler_not_found(self, engine, state_store):
        """Test handling events with no registered handlers."""
        await engine.initialize()

        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            pass

        # Shipping event has no handler
        event = OrderShipped(order_id="order-1")

        # Should not raise
        await engine.handle_event(event)

    @pytest.mark.asyncio
    async def test_health_check(self, engine, state_store):
        """Test projection health status."""
        # Before initialization
        assert engine.is_healthy() is False

        await engine.initialize()
        assert engine.is_healthy() is True

        # After error
        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            raise ValueError("Test error")

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )

        try:
            await engine.handle_event(event)
        except ValueError:
            pass

        assert engine.is_healthy() is False

    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, engine, state_store):
        """Test processing multiple events concurrently."""
        await engine.initialize()

        processed_events: list[str] = []

        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            await asyncio.sleep(0.01)  # Simulate async work
            processed_events.append(event.order_id)

        events = [
            OrderCreated(order_id=f"order-{i}", customer_id="customer-1", amount=100.0)
            for i in range(10)
        ]

        # Process sequentially (as per projection model)
        await engine.process_events(events)

        assert len(processed_events) == 10

    @pytest.mark.asyncio
    async def test_different_event_types(self, engine, state_store):
        """Test handling different event types."""
        await engine.initialize()

        created_events: list[OrderCreated] = []
        shipped_events: list[OrderShipped] = []
        cancelled_events: list[OrderCancelled] = []

        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            created_events.append(event)

        @engine.on(OrderShipped)
        async def handle_shipped(event: OrderShipped) -> None:
            shipped_events.append(event)

        @engine.on(OrderCancelled)
        async def handle_cancelled(event: OrderCancelled) -> None:
            cancelled_events.append(event)

        events = [
            OrderCreated(order_id="order-1", customer_id="customer-1", amount=100.0),
            OrderShipped(order_id="order-1"),
            OrderCancelled(order_id="order-2", reason="Out of stock"),
            OrderCreated(order_id="order-3", customer_id="customer-1", amount=300.0),
        ]

        await engine.process_events(events)

        assert len(created_events) == 2
        assert len(shipped_events) == 1
        assert len(cancelled_events) == 1

    @pytest.mark.asyncio
    async def test_state_restoration(self, engine, state_store):
        """Test restoring projection from saved state."""
        # First engine instance
        await engine.initialize()

        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            pass

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )
        await engine.handle_event(event)

        # Create new engine instance
        engine2 = ProjectionEngine("test-projection", state_store)
        await engine2.initialize()

        state = engine2.get_state()
        assert state is not None
        assert state.last_processed_event_id == event.id

    @pytest.mark.asyncio
    async def test_no_tracing_provider(self, state_store):
        """Test projection engine without tracing provider."""
        engine = ProjectionEngine("test-projection", state_store)
        await engine.initialize()

        call_log: list[OrderCreated] = []

        @engine.on(OrderCreated)
        async def handle_created(event: OrderCreated) -> None:
            call_log.append(event)

        event = OrderCreated(
            order_id="order-1", customer_id="customer-1", amount=100.0
        )
        await engine.handle_event(event)

        assert len(call_log) == 1


class TestInMemoryProjectionStateStore:
    """Tests for InMemoryProjectionStateStore."""

    def test_initialization(self):
        """Test state store initialization."""
        store = InMemoryProjectionStateStore()
        assert store is not None

    @pytest.mark.asyncio
    async def test_save_and_load(self):
        """Test saving and loading projection state."""
        store = InMemoryProjectionStateStore()

        state = ProjectionState(projection_id="test-projection")
        await store.save_state(state)

        loaded_state = await store.load_state("test-projection")
        assert loaded_state is not None
        assert loaded_state.projection_id == "test-projection"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self):
        """Test loading nonexistent state returns None."""
        store = InMemoryProjectionStateStore()
        loaded_state = await store.load_state("nonexistent")
        assert loaded_state is None

    @pytest.mark.asyncio
    async def test_update_state(self):
        """Test updating existing state."""
        store = InMemoryProjectionStateStore()

        state = ProjectionState(projection_id="test-projection")
        await store.save_state(state)

        # Update state
        updated_state = ProjectionState(
            projection_id="test-projection",
            last_processed_event_id="event-123",
        )
        await store.save_state(updated_state)

        loaded_state = await store.load_state("test-projection")
        assert loaded_state is not None
        assert loaded_state.last_processed_event_id == "event-123"
