"""Benchmark event store operations.

Tests the performance of event saving, loading, and snapshot operations.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from orchestrix.infrastructure import InMemoryEventStore
from orchestrix.message import Event
from orchestrix.snapshot import Snapshot


@dataclass(frozen=True)
class BenchmarkEvent:
    """Simple event for benchmarking."""

    value: int


# ========================================
# Single Event Operations
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_single_event(benchmark):
    """Benchmark saving a single event."""
    store = InMemoryEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    event = Event(
        id=str(uuid.uuid4()),
        type="BenchmarkEvent",
        source="/benchmark",
        subject=aggregate_id,
        data=BenchmarkEvent(value=1),
        timestamp=datetime.now(timezone.utc),
    )

    async def save():
        await store.save_async(aggregate_id, [event])

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_single_event(benchmark):
    """Benchmark loading a single event."""
    store = InMemoryEventStore()
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
    asyncio.run(store.save_async(aggregate_id, [event]))

    async def load():
        return await store.load_async(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Batch Operations
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_100_events(benchmark):
    """Benchmark saving 100 events."""
    store = InMemoryEventStore()
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

    async def save():
        await store.save_async(aggregate_id, events)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_100_events(benchmark):
    """Benchmark loading 100 events."""
    store = InMemoryEventStore()
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
    asyncio.run(store.save_async(aggregate_id, events))

    async def load():
        return await store.load_async(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


@pytest.mark.benchmark(group="event-store")
def test_save_1000_events(benchmark):
    """Benchmark saving 1,000 events."""
    store = InMemoryEventStore()
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

    async def save():
        await store.save_async(aggregate_id, events)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_1000_events(benchmark):
    """Benchmark loading 1,000 events."""
    store = InMemoryEventStore()
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
    asyncio.run(store.save_async(aggregate_id, events))

    async def load():
        return await store.load_async(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Large Event Stream Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_10000_events(benchmark):
    """Benchmark saving 10,000 events (throughput test)."""
    store = InMemoryEventStore()
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

    async def save():
        await store.save_async(aggregate_id, events)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_10000_events(benchmark):
    """Benchmark loading 10,000 events."""
    store = InMemoryEventStore()
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
    asyncio.run(store.save_async(aggregate_id, events))

    async def load():
        return await store.load_async(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Partial Load Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_load_from_version_100(benchmark):
    """Benchmark loading from version 100 onwards."""
    store = InMemoryEventStore()
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
    asyncio.run(store.save_async(aggregate_id, events))

    async def load():
        return await store.load_async(aggregate_id, from_version=100)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Snapshot Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_snapshot(benchmark):
    """Benchmark saving a snapshot."""
    store = InMemoryEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    snapshot = Snapshot(
        aggregate_id=aggregate_id, version=100, state={"counter": 100}
    )

    async def save():
        await store.save_snapshot_async(snapshot)

    benchmark(lambda: asyncio.run(save()))


@pytest.mark.benchmark(group="event-store")
def test_load_snapshot(benchmark):
    """Benchmark loading a snapshot."""
    store = InMemoryEventStore()
    aggregate_id = f"agg-{uuid.uuid4()}"
    snapshot = Snapshot(
        aggregate_id=aggregate_id, version=100, state={"counter": 100}
    )

    # Pre-populate store
    asyncio.run(store.save_snapshot_async(snapshot))

    async def load():
        return await store.load_snapshot_async(aggregate_id)

    benchmark(lambda: asyncio.run(load()))


# ========================================
# Multiple Aggregates Benchmarks
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_save_100_aggregates(benchmark):
    """Benchmark saving events to 100 different aggregates."""
    store = InMemoryEventStore()

    async def save_many():
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
            await store.save_async(aggregate_id, [event])

    benchmark(lambda: asyncio.run(save_many()))


@pytest.mark.benchmark(group="event-store")
def test_load_100_aggregates(benchmark):
    """Benchmark loading events from 100 different aggregates."""
    store = InMemoryEventStore()

    # Pre-populate store with 100 aggregates
    async def populate():
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
            await store.save_async(aggregate_id, [event])

    asyncio.run(populate())

    async def load_many():
        for i in range(100):
            aggregate_id = f"agg-{i}"
            await store.load_async(aggregate_id)

    benchmark(lambda: asyncio.run(load_many()))


# ========================================
# Concurrent Operations
# ========================================


@pytest.mark.benchmark(group="event-store")
def test_concurrent_save_10_aggregates(benchmark):
    """Benchmark concurrent saves to 10 aggregates."""
    store = InMemoryEventStore()

    async def concurrent_save():
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
            tasks.append(store.save_async(aggregate_id, [event]))
        await asyncio.gather(*tasks)

    benchmark(lambda: asyncio.run(concurrent_save()))


@pytest.mark.benchmark(group="event-store")
def test_concurrent_load_10_aggregates(benchmark):
    """Benchmark concurrent loads from 10 aggregates."""
    store = InMemoryEventStore()

    # Pre-populate store
    async def populate():
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
            await store.save_async(aggregate_id, [event])

    asyncio.run(populate())

    async def concurrent_load():
        tasks = [store.load_async(f"agg-{i}") for i in range(10)]
        await asyncio.gather(*tasks)

    benchmark(lambda: asyncio.run(concurrent_load()))
