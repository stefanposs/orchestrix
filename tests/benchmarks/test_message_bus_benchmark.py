"""Benchmark message bus throughput.

Tests the performance of message publishing and handling.
"""

import asyncio
from dataclasses import dataclass

import pytest

from orchestrix.infrastructure.async_inmemory_bus import InMemoryAsyncMessageBus
from orchestrix.core.message import Message


@dataclass(frozen=True, kw_only=True)
class BenchmarkCommand(Message):
    """Simple command for benchmarking."""

    command_id: str
    payload: str


@dataclass(frozen=True, kw_only=True)
class BenchmarkEvent(Message):
    """Simple event for benchmarking."""

    event_id: str
    data: dict


# ========================================
# Single Message Benchmarks
# ========================================


@pytest.mark.benchmark(group="message-bus")
def test_publish_single_command(benchmark):
    """Benchmark publishing a single command."""
    bus = InMemoryAsyncMessageBus()
    command = BenchmarkCommand(command_id="bench-1", payload="test data")

    # Handler that does nothing
    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def publish():
        await bus.publish(command)

    benchmark(lambda: asyncio.run(publish()))


@pytest.mark.benchmark(group="message-bus")
def test_publish_single_event(benchmark):
    """Benchmark publishing a single event."""
    bus = InMemoryAsyncMessageBus()
    event = BenchmarkEvent(event_id="bench-1", data={"key": "value"})

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkEvent, noop_handler)

    async def publish():
        await bus.publish(event)

    benchmark(lambda: asyncio.run(publish()))


# ========================================
# Batch Publishing Benchmarks
# ========================================


@pytest.mark.benchmark(group="message-bus")
def test_publish_100_messages(benchmark):
    """Benchmark publishing 100 messages."""
    bus = InMemoryAsyncMessageBus()
    messages = [
        BenchmarkCommand(command_id=f"bench-{i}", payload=f"data-{i}")
        for i in range(100)
    ]

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def publish_batch():
        for msg in messages:
            await bus.publish(msg)

    benchmark(lambda: asyncio.run(publish_batch()))


@pytest.mark.benchmark(group="message-bus")
def test_publish_1000_messages(benchmark):
    """Benchmark publishing 1,000 messages (throughput test)."""
    bus = InMemoryAsyncMessageBus()
    messages = [
        BenchmarkCommand(command_id=f"bench-{i}", payload=f"data-{i}")
        for i in range(1000)
    ]

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def publish_batch():
        for msg in messages:
            await bus.publish(msg)

    benchmark(lambda: asyncio.run(publish_batch()))


# ========================================
# Multiple Handlers Benchmarks
# ========================================


@pytest.mark.benchmark(group="message-bus")
def test_publish_with_5_handlers(benchmark):
    """Benchmark message with 5 concurrent handlers."""
    bus = InMemoryAsyncMessageBus()
    command = BenchmarkCommand(command_id="bench-1", payload="test")

    # Register 5 handlers
    for i in range(5):

        async def handler(_msg, idx=i):  # noqa: ARG001
            await asyncio.sleep(0)  # Yield control

        bus.subscribe(BenchmarkCommand, handler)

    async def publish():
        await bus.publish(command)

    benchmark(lambda: asyncio.run(publish()))


@pytest.mark.benchmark(group="message-bus")
def test_publish_with_10_handlers(benchmark):
    """Benchmark message with 10 concurrent handlers."""
    bus = InMemoryAsyncMessageBus()
    command = BenchmarkCommand(command_id="bench-1", payload="test")

    # Register 10 handlers
    for i in range(10):

        async def handler(_msg, idx=i):  # noqa: ARG001
            await asyncio.sleep(0)

        bus.subscribe(BenchmarkCommand, handler)

    async def publish():
        await bus.publish(command)

    benchmark(lambda: asyncio.run(publish()))


# ========================================
# Message Size Benchmarks
# ========================================


@pytest.mark.benchmark(group="message-bus")
def test_publish_small_payload(benchmark):
    """Benchmark message with small payload (<1KB)."""
    bus = InMemoryAsyncMessageBus()
    command = BenchmarkCommand(command_id="bench-1", payload="x" * 100)

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def publish():
        await bus.publish(command)

    benchmark(lambda: asyncio.run(publish()))


@pytest.mark.benchmark(group="message-bus")
def test_publish_medium_payload(benchmark):
    """Benchmark message with medium payload (~10KB)."""
    bus = InMemoryAsyncMessageBus()
    command = BenchmarkCommand(command_id="bench-1", payload="x" * 10000)

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def publish():
        await bus.publish(command)

    benchmark(lambda: asyncio.run(publish()))


@pytest.mark.benchmark(group="message-bus")
def test_publish_large_payload(benchmark):
    """Benchmark message with large payload (~100KB)."""
    bus = InMemoryAsyncMessageBus()
    command = BenchmarkCommand(command_id="bench-1", payload="x" * 100000)

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def publish():
        await bus.publish(command)

    benchmark(lambda: asyncio.run(publish()))


# ========================================
# Concurrent Publishing Benchmarks
# ========================================


@pytest.mark.benchmark(group="message-bus")
def test_concurrent_publish_10_messages(benchmark):
    """Benchmark 10 concurrent publishes."""
    bus = InMemoryAsyncMessageBus()

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def concurrent_publish():
        tasks = [
            bus.publish(
                BenchmarkCommand(command_id=f"bench-{i}", payload=f"data-{i}")
            )
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

    benchmark(lambda: asyncio.run(concurrent_publish()))


@pytest.mark.benchmark(group="message-bus")
def test_concurrent_publish_100_messages(benchmark):
    """Benchmark 100 concurrent publishes."""
    bus = InMemoryAsyncMessageBus()

    async def noop_handler(_msg):
        pass

    bus.subscribe(BenchmarkCommand, noop_handler)

    async def concurrent_publish():
        tasks = [
            bus.publish(
                BenchmarkCommand(command_id=f"bench-{i}", payload=f"data-{i}")
            )
            for i in range(100)
        ]
        await asyncio.gather(*tasks)

    benchmark(lambda: asyncio.run(concurrent_publish()))
