"""Benchmark event store operations.

Tests the performance of event saving, loading, and snapshot operations.
"""

import asyncio
import uuid
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from orchestrix.infrastructure.memory.async_store import InMemoryAsyncEventStore
from orchestrix.core.messaging.message import Event
from orchestrix.core.eventsourcing.snapshot import Snapshot


@dataclass(frozen=True)
class BenchmarkEvent:
    """Simple event for benchmarking."""

    value: int


# ========================================
# Single Event Operations
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_single_event(benchmark: Any) -> None:
    """Benchmark saving a single event."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    event = Event(
        id=str(uuid.uuid4()),
        type="BenchmarkEvent",
        source="/benchmark",
        subject=aggregate_id,
        data=BenchmarkEvent(value=1),
        timestamp=datetime.now(timezone.utc),
    )

    async def save() -> None:
        await store.save(aggregate_id, [event])

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_single_event(benchmark: Any) -> None:
    """Benchmark loading a single event."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    event = Event(
        id=str(uuid.uuid4()),
        type="BenchmarkEvent",
        source="/benchmark",
        subject=aggregate_id,
        data=BenchmarkEvent(value=1),
        timestamp=datetime.now(timezone.utc),
    )

    # Pre-populate store
    asyncio.run(store.save(aggregate_id, [event]))

    async def load() -> list[Event]:
        return await store.load(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Batch Operations
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_100_events(benchmark: Any) -> None:
    """Benchmark saving 100 events."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    events = [
        Event(
            id=str(uuid.uuid4()),
            type="BenchmarkEvent",
            source="/benchmark",
            subject=aggregate_id,
            data=BenchmarkEvent(value=i),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(100)
    ]

    async def save() -> None:
        await store.save(aggregate_id, events)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_100_events(benchmark: Any) -> None:
    """Benchmark loading 100 events."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    events = [
        Event(
            id=str(uuid.uuid4()),
            type="BenchmarkEvent",
            source="/benchmark",
            subject=aggregate_id,
            data=BenchmarkEvent(value=i),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(100)
    ]

    # Pre-populate store
    asyncio.run(store.save(aggregate_id, events))

    async def load() -> list[Event]:
        return await store.load(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


@pytest.mark.benchmark(group="event-store")
def test_save_1000_events(benchmark: Any) -> None:
    """Benchmark saving 1,000 events."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    events = [
        Event(
            id=str(uuid.uuid4()),
            type="BenchmarkEvent",
            source="/benchmark",
            subject=aggregate_id,
            data=BenchmarkEvent(value=i),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(1000)
    ]

    async def save() -> None:
        await store.save(aggregate_id, events)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_1000_events(benchmark: Any) -> None:
    """Benchmark loading 1,000 events."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    events = [
        Event(
            id=str(uuid.uuid4()),
            type="BenchmarkEvent",
            source="/benchmark",
            subject=aggregate_id,
            data=BenchmarkEvent(value=i),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(1000)
    ]

    # Pre-populate store
    asyncio.run(store.save(aggregate_id, events))

    async def load() -> list[Event]:
        return await store.load(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Large Event Stream Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_10000_events(benchmark: Any) -> None:
    """Benchmark saving 10,000 events (throughput test)."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    events = [
        Event(
            id=str(uuid.uuid4()),
            type="BenchmarkEvent",
            source="/benchmark",
            subject=aggregate_id,
            data=BenchmarkEvent(value=i),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(10000)
    ]

    async def save() -> None:
        await store.save(aggregate_id, events)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_10000_events(benchmark: Any) -> None:
    """Benchmark loading 10,000 events."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    events = [
        Event(
            id=str(uuid.uuid4()),
            type="BenchmarkEvent",
            source="/benchmark",
            subject=aggregate_id,
            data=BenchmarkEvent(value=i),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(10000)
    ]

    # Pre-populate store
    asyncio.run(store.save(aggregate_id, events))

    async def load() -> list[Event]:
        return await store.load(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Partial Load Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_load_from_version_100(benchmark: Any) -> None:
    """Benchmark loading from version 100 onwards."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    events = [
        Event(
            id=str(uuid.uuid4()),
            type="BenchmarkEvent",
            source="/benchmark",
            subject=aggregate_id,
            data=BenchmarkEvent(value=i),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(1000)
    ]

    # Pre-populate store
    asyncio.run(store.save(aggregate_id, events))

    async def load() -> list[Event]:
        return await store.load(aggregate_id, from_version=100)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Snapshot Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_snapshot(benchmark: Any) -> None:
    """Benchmark saving a snapshot."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    snapshot = Snapshot(
        aggregate_id=aggregate_id,
        aggregate_type="BenchmarkAggregate",
        version=100,
        state={"counter": 100},
    )

    async def save() -> None:
        await store.save_snapshot(snapshot)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_snapshot(benchmark: Any) -> None:
    """Benchmark loading a snapshot."""
    store = InMemoryAsyncEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    snapshot = Snapshot(
        aggregate_id=aggregate_id,
        aggregate_type="BenchmarkAggregate",
        version=100,
        state={"counter": 100},
    )

    # Pre-populate store
    asyncio.run(store.save_snapshot(snapshot))

    async def load() -> Snapshot | None:
        return await store.load_snapshot(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Multiple Aggregates Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_100_aggregates(benchmark: Any) -> None:
    """Benchmark saving events to 100 different aggregates."""
    store = InMemoryAsyncEventStore()

    async def save_many() -> None:
        for i in range(100):
            aggregate_id = f"agg-{i}"
            event = Event(
                id=str(uuid.uuid4()),
                type="BenchmarkEvent",
                source="/benchmark",
                subject=aggregate_id,
                data=BenchmarkEvent(value=i),
                timestamp=datetime.now(timezone.utc),
            )
            await store.save(aggregate_id, [event])

    benchmark(lambda: asyncio.run(save_many()))


@pytest.mark.benchmark(group="event-store")
def test_load_100_aggregates(benchmark: Any) -> None:
    """Benchmark loading events from 100 different aggregates."""
    store = InMemoryAsyncEventStore()

    # Pre-populate store with 100 aggregates
    async def populate() -> None:
        for i in range(100):
            aggregate_id = f"agg-{i}"
            event = Event(
                id=str(uuid.uuid4()),
                type="BenchmarkEvent",
                source="/benchmark",
                subject=aggregate_id,
                data=BenchmarkEvent(value=i),
                timestamp=datetime.now(timezone.utc),
            )
            await store.save(aggregate_id, [event])

    asyncio.run(populate())

    async def load_many() -> None:
        for i in range(100):
            aggregate_id = f"agg-{i}"
            await store.load(aggregate_id)

    benchmark(lambda: asyncio.run(load_many()))


# ========================================
# Concurrent Operations
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_concurrent_save_10_aggregates(benchmark: Any) -> None:
    """Benchmark concurrent saves to 10 aggregates."""
    store = InMemoryAsyncEventStore()

    async def concurrent_save() -> None:
        tasks = []
        for i in range(10):
            aggregate_id = f"agg-{i}"
            event = Event(
                id=str(uuid.uuid4()),
                type="BenchmarkEvent",
                source="/benchmark",
                subject=aggregate_id,
                data=BenchmarkEvent(value=i),
                timestamp=datetime.now(timezone.utc),
            )
            tasks.append(store.save(aggregate_id, [event]))
        await asyncio.gather(*tasks)

    benchmark(lambda: asyncio.run(concurrent_save()))


@pytest.mark.benchmark(group="event-store")
def test_concurrent_load_10_aggregates(benchmark: Any) -> None:
    """Benchmark concurrent loads from 10 aggregates."""
    store = InMemoryAsyncEventStore()

    # Pre-populate store
    async def populate() -> None:
        for i in range(10):
            aggregate_id = f"agg-{i}"
            event = Event(
                id=str(uuid.uuid4()),
                type="BenchmarkEvent",
                source="/benchmark",
                subject=aggregate_id,
                data=BenchmarkEvent(value=i),
                timestamp=datetime.now(timezone.utc),
            )
            await store.save(aggregate_id, [event])

    asyncio.run(populate())

    async def concurrent_load() -> None:
        tasks = [store.load(f"agg-{i}") for i in range(10)]
        await asyncio.gather(*tasks)

    benchmark(lambda: asyncio.run(concurrent_load()))
