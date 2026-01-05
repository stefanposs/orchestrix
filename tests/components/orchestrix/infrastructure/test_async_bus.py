"""Tests for async message bus."""

import asyncio
import time

import pytest
from orchestrix.core.common.exceptions import HandlerError
from orchestrix.core.messaging.message import Command
from orchestrix.infrastructure.memory.async_bus import InMemoryAsyncMessageBus


@pytest.fixture
def async_bus() -> InMemoryAsyncMessageBus:
    """Provide a fresh InMemoryAsyncMessageBus for each test."""
    return InMemoryAsyncMessageBus()


class CreateOrderAsync(Command):
    """Test async command."""

    order_id: str = "test-123"


class TestAsyncMessageBus:
    """Test async message bus."""

    @pytest.mark.asyncio
    async def test_async_publish_calls_single_handler(
        self, async_bus: InMemoryAsyncMessageBus
    ) -> None:
        """Test publishing to a single async handler."""
        results = []

        async def handler(msg: CreateOrderAsync) -> None:
            results.append(msg.order_id)

        async_bus.subscribe(CreateOrderAsync, handler)
        await async_bus.publish(CreateOrderAsync())

        assert len(results) == 1
        assert results[0] == "test-123"

    @pytest.mark.asyncio
    async def test_async_publish_calls_multiple_handlers(
        self, async_bus: InMemoryAsyncMessageBus
    ) -> None:
        """Test publishing to multiple async handlers."""
        results = []

        async def handler1(msg: Command) -> None:
            results.append("handler1")

        async def handler2(msg: Command) -> None:
            results.append("handler2")

        async_bus.subscribe(CreateOrderAsync, handler1)
        async_bus.subscribe(CreateOrderAsync, handler2)

        await async_bus.publish(CreateOrderAsync())

        assert len(results) == 2
        assert set(results) == {"handler1", "handler2"}

    @pytest.mark.asyncio
    async def test_handlers_execute_concurrently(self, async_bus: InMemoryAsyncMessageBus) -> None:
        """Test that multiple handlers execute in parallel, not sequentially."""
        timing = []

        async def slow_handler1(msg: Command) -> None:
            timing.append(("h1_start", time.time()))
            await asyncio.sleep(0.1)
            timing.append(("h1_end", time.time()))

        async def slow_handler2(msg: Command) -> None:
            timing.append(("h2_start", time.time()))
            await asyncio.sleep(0.1)
            timing.append(("h2_end", time.time()))

        async_bus.subscribe(CreateOrderAsync, slow_handler1)
        async_bus.subscribe(CreateOrderAsync, slow_handler2)

        start = time.time()
        await async_bus.publish(CreateOrderAsync())
        elapsed = time.time() - start

        # If handlers ran sequentially: ~0.2s
        # If handlers ran concurrently: ~0.1s
        # Allow some margin for overhead
        assert elapsed < 0.15, f"Handlers did not run concurrently: {elapsed}s"

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_stop_other_handlers(
        self, async_bus: InMemoryAsyncMessageBus
    ) -> None:
        """Test that one handler failing doesn't prevent others from running."""
        results = []

        async def failing_handler(msg: Command) -> None:
            msg_text = "Handler failed"
            raise ValueError(msg_text)

        async def success_handler(msg: CreateOrderAsync) -> None:
            results.append(msg.order_id)

        async_bus.subscribe(CreateOrderAsync, failing_handler)
        async_bus.subscribe(CreateOrderAsync, success_handler)

        # Should not raise - error is logged but doesn't stop execution
        await async_bus.publish(CreateOrderAsync())

        # Success handler should have run
        assert len(results) == 1
        assert results[0] == "test-123"

    @pytest.mark.asyncio
    async def test_all_handlers_fail_raises_error(self, async_bus: InMemoryAsyncMessageBus) -> None:
        """Test that if all handlers fail, an error is raised."""

        async def failing_handler_1(msg: Command) -> None:
            msg_text = "Handler 1 failed"
            raise ValueError(msg_text)

        async def failing_handler_2(msg: Command) -> None:
            msg_text = "Handler 2 failed"
            raise RuntimeError(msg_text)

        async_bus.subscribe(CreateOrderAsync, failing_handler_1)
        async_bus.subscribe(CreateOrderAsync, failing_handler_2)

        with pytest.raises(HandlerError) as exc_info:
            await async_bus.publish(CreateOrderAsync())

        assert "all_handlers" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_handlers_does_not_raise(self, async_bus: InMemoryAsyncMessageBus) -> None:
        """Test that publishing with no handlers doesn't raise."""
        # Should not raise
        await async_bus.publish(CreateOrderAsync())

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure_handlers(
        self, async_bus: InMemoryAsyncMessageBus
    ) -> None:
        """Test that partial handler failures don't prevent other handlers."""
        results = []

        async def handler1(msg: Command) -> None:
            results.append("handler1")

        async def handler2(msg: Command) -> None:
            msg_text = "Handler 2 failed"
            raise ValueError(msg_text)

        async def handler3(msg: Command) -> None:
            results.append("handler3")

        async_bus.subscribe(CreateOrderAsync, handler1)
        async_bus.subscribe(CreateOrderAsync, handler2)
        async_bus.subscribe(CreateOrderAsync, handler3)

        # Should not raise
        await async_bus.publish(CreateOrderAsync())

        # Successful handlers should have run
        assert set(results) == {"handler1", "handler3"}

    @pytest.mark.asyncio
    async def test_only_matching_message_type_handlers_called(
        self, async_bus: InMemoryAsyncMessageBus
    ) -> None:
        """Test that only handlers for the matching message type are called."""
        results = []

        class OrderConfirmed(Command):
            pass

        async def order_created_handler(msg: Command) -> None:
            results.append("order_created")

        async def order_confirmed_handler(msg: Command) -> None:
            results.append("order_confirmed")

        async_bus.subscribe(CreateOrderAsync, order_created_handler)
        async_bus.subscribe(OrderConfirmed, order_confirmed_handler)

        await async_bus.publish(CreateOrderAsync())

        assert results == ["order_created"]

    @pytest.mark.asyncio
    async def test_high_message_throughput(self, async_bus: InMemoryAsyncMessageBus) -> None:
        """Test async bus with high message volume."""
        counter = {"value": 0}

        async def counting_handler(_: Command) -> None:
            counter["value"] += 1

        async_bus.subscribe(CreateOrderAsync, counting_handler)

        # Publish 100 messages concurrently
        tasks = [async_bus.publish(CreateOrderAsync()) for _ in range(100)]
        await asyncio.gather(*tasks)

        assert counter["value"] == 100

    @pytest.mark.asyncio
    async def test_subscription_persists_across_publishes(
        self, async_bus: InMemoryAsyncMessageBus
    ) -> None:
        """Test that subscriptions persist across multiple publishes."""
        results = []

        async def handler(msg: CreateOrderAsync) -> None:
            results.append(msg.order_id)

        async_bus.subscribe(CreateOrderAsync, handler)

        # First publish
        await async_bus.publish(CreateOrderAsync())
        # Second publish
        await async_bus.publish(CreateOrderAsync())

        assert len(results) == 2
        assert results[0] == "test-123"
        assert results[1] == "test-123"
