"""Integration tests for PostgreSQL Event Store.

These tests require a PostgreSQL instance. Run with:
    pytest tests/integration/test_postgres_store.py --integration

Or with docker:
    docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test postgres:15
    pytest tests/integration/test_postgres_store.py --integration
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from orchestrix.core.exceptions import ConcurrencyError
from orchestrix.core.message import Event

# Check for postgres dependency
asyncpg = pytest.importorskip("asyncpg", reason="asyncpg not installed")

# Import after checking dependency
from orchestrix.infrastructure.postgres_store import PostgreSQLEventStore

# Get connection string from environment or use default
POSTGRES_DSN = os.getenv(
    "POSTGRES_TEST_DSN",
    "postgresql://postgres:test@localhost:5432/orchestrix_test"
)


# Test Events
@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    """Test event for order creation."""
    order_id: str
    customer_id: str
    amount: Decimal


@dataclass(frozen=True, kw_only=True)
class OrderUpdated(Event):
    """Test event for order update."""
    order_id: str
    status: str


@dataclass(frozen=True, kw_only=True)
class ItemAdded(Event):
    """Test event for item addition."""
    order_id: str
    item_id: str
    quantity: int


@pytest.fixture
async def store():
    """Create PostgreSQL store and clean up after test."""
    store = PostgreSQLEventStore(
        connection_string=POSTGRES_DSN,
        pool_min_size=2,
        pool_max_size=5,
    )
    
    try:
        await store.initialize()
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
    
    # Clean up before test
    async with store._pool.acquire() as conn:
        await conn.execute("DELETE FROM events")
        await conn.execute("DELETE FROM snapshots")
    
    yield store
    
    # Clean up after test
    async with store._pool.acquire() as conn:
        await conn.execute("DELETE FROM events")
        await conn.execute("DELETE FROM snapshots")
    
    await store.close()


@pytest.mark.asyncio
@pytest.mark.integration
class TestPostgreSQLStoreBasics:
    """Basic event store operations."""

    async def test_save_and_load_single_event(self, store):
        """Test saving and loading a single event."""
        event = OrderCreated(
            order_id="order-001",
            customer_id="cust-001",
            amount=Decimal("99.99"),
        )
        
        await store.save_async("order-001", [event])
        loaded = await store.load_async("order-001")
        
        assert len(loaded) == 1
        assert loaded[0].data["order_id"] == "order-001"
        assert loaded[0].data["customer_id"] == "cust-001"
        assert Decimal(loaded[0].data["amount"]) == Decimal("99.99")

    async def test_save_and_load_multiple_events(self, store):
        """Test saving and loading multiple events."""
        events = [
            OrderCreated(
                order_id="order-002",
                customer_id="cust-002",
                amount=Decimal("149.99"),
            ),
            ItemAdded(
                order_id="order-002",
                item_id="item-001",
                quantity=2,
            ),
            OrderUpdated(
                order_id="order-002",
                status="confirmed",
            ),
        ]
        
        await store.save_async("order-002", events)
        loaded = await store.load_async("order-002")
        
        assert len(loaded) == 3
        assert loaded[0].type == "OrderCreated"
        assert loaded[1].type == "ItemAdded"
        assert loaded[2].type == "OrderUpdated"

    async def test_load_nonexistent_aggregate(self, store):
        """Test loading events for non-existent aggregate."""
        loaded = await store.load_async("nonexistent")
        assert loaded == []

    async def test_multiple_aggregates_isolated(self, store):
        """Test that different aggregates are isolated."""
        event1 = OrderCreated(
            order_id="order-010",
            customer_id="cust-010",
            amount=Decimal("10.00"),
        )
        event2 = OrderCreated(
            order_id="order-020",
            customer_id="cust-020",
            amount=Decimal("20.00"),
        )
        
        await store.save_async("order-010", [event1])
        await store.save_async("order-020", [event2])
        
        loaded1 = await store.load_async("order-010")
        loaded2 = await store.load_async("order-020")
        
        assert len(loaded1) == 1
        assert len(loaded2) == 1
        assert loaded1[0].data["order_id"] == "order-010"
        assert loaded2[0].data["order_id"] == "order-020"

    async def test_event_ordering_preserved(self, store):
        """Test that event order is preserved."""
        events = [
            OrderCreated(
                order_id=f"order-{i}",
                customer_id=f"cust-{i}",
                amount=Decimal(str(i)),
            )
            for i in range(100)
        ]
        
        await store.save_async("order-batch", events)
        loaded = await store.load_async("order-batch")
        
        assert len(loaded) == 100
        for i, event in enumerate(loaded):
            assert Decimal(event.data["amount"]) == Decimal(str(i))


@pytest.mark.asyncio
@pytest.mark.integration
class TestOptimisticLocking:
    """Test optimistic concurrency control."""

    async def test_expected_version_match_succeeds(self, store):
        """Test that save succeeds when expected_version matches."""
        # Create initial event
        event1 = OrderCreated(
            order_id="order-100",
            customer_id="cust-100",
            amount=Decimal("100.00"),
        )
        await store.save_async("order-100", [event1])
        
        # Load to get current version (should be 0)
        loaded = await store.load_async("order-100")
        assert len(loaded) == 1
        
        # Save with correct expected_version
        event2 = OrderUpdated(order_id="order-100", status="confirmed")
        await store.save_async("order-100", [event2], expected_version=0)
        
        # Verify both events exist
        all_events = await store.load_async("order-100")
        assert len(all_events) == 2

    async def test_expected_version_mismatch_raises_error(self, store):
        """Test that ConcurrencyError is raised on version mismatch."""
        # Create initial events
        events = [
            OrderCreated(
                order_id="order-200",
                customer_id="cust-200",
                amount=Decimal("200.00"),
            ),
            ItemAdded(
                order_id="order-200",
                item_id="item-200",
                quantity=1,
            ),
        ]
        await store.save_async("order-200", events)
        
        # Try to save with wrong expected_version
        event = OrderUpdated(order_id="order-200", status="cancelled")
        
        with pytest.raises(ConcurrencyError) as exc_info:
            await store.save_async("order-200", [event], expected_version=0)
        
        assert exc_info.value.aggregate_id == "order-200"
        assert exc_info.value.expected_version == 0
        assert exc_info.value.actual_version == 1  # Two events were saved

    async def test_concurrent_append_with_optimistic_locking(self, store):
        """Test that concurrent writes are handled correctly."""
        # Create initial event
        event1 = OrderCreated(
            order_id="order-300",
            customer_id="cust-300",
            amount=Decimal("300.00"),
        )
        await store.save_async("order-300", [event1])
        
        # Simulate two concurrent writers
        event2 = OrderUpdated(order_id="order-300", status="pending")
        event3 = ItemAdded(order_id="order-300", item_id="item-300", quantity=1)
        
        # Both try to write at the same time with same expected_version
        task1 = store.save_async("order-300", [event2], expected_version=0)
        task2 = store.save_async("order-300", [event3], expected_version=0)
        
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        
        # One should succeed, one should fail
        successes = [r for r in results if r is None]
        failures = [r for r in results if isinstance(r, ConcurrencyError)]
        
        assert len(successes) == 1, "Exactly one write should succeed"
        assert len(failures) == 1, "Exactly one write should fail"
        
        # Verify only 2 events exist (initial + one concurrent)
        all_events = await store.load_async("order-300")
        assert len(all_events) == 2

    async def test_no_expected_version_always_succeeds(self, store):
        """Test that save without expected_version always succeeds."""
        # Create initial events
        for i in range(5):
            event = OrderCreated(
                order_id=f"order-400-{i}",
                customer_id=f"cust-400",
                amount=Decimal("400.00"),
            )
            await store.save_async("order-400", [event])  # No expected_version
        
        # All saves should succeed
        loaded = await store.load_async("order-400")
        assert len(loaded) == 5


@pytest.mark.asyncio
@pytest.mark.integration
class TestConcurrency:
    """Test concurrent operations."""

    async def test_concurrent_writes_different_aggregates(self, store):
        """Test concurrent writes to different aggregates."""
        async def write_events(aggregate_id: str):
            for i in range(10):
                event = OrderCreated(
                    order_id=f"{aggregate_id}-{i}",
                    customer_id=f"cust-{i}",
                    amount=Decimal("100.00"),
                )
                await store.save_async(aggregate_id, [event])
        
        # Write to 10 different aggregates concurrently
        tasks = [write_events(f"agg-{i}") for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Verify all writes succeeded
        for i in range(10):
            events = await store.load_async(f"agg-{i}")
            assert len(events) == 10

    async def test_concurrent_reads(self, store):
        """Test concurrent reads of same aggregate."""
        # Create events
        events = [
            OrderCreated(
                order_id="order-500",
                customer_id="cust-500",
                amount=Decimal("500.00"),
            )
            for _ in range(100)
        ]
        await store.save_async("order-500", events)
        
        # Read concurrently 50 times
        tasks = [store.load_async("order-500") for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # All reads should return same data
        for loaded in results:
            assert len(loaded) == 100

    async def test_mixed_reads_and_writes(self, store):
        """Test mixed concurrent reads and writes."""
        # Initial event
        event1 = OrderCreated(
            order_id="order-600",
            customer_id="cust-600",
            amount=Decimal("600.00"),
        )
        await store.save_async("order-600", [event1])
        
        async def write():
            for i in range(5):
                event = ItemAdded(
                    order_id="order-600",
                    item_id=f"item-{i}",
                    quantity=i,
                )
                while True:
                    try:
                        await store.save_async("order-600", [event])
                        break
                    except ConcurrencyError:
                        await asyncio.sleep(0.01)  # Retry
                await asyncio.sleep(0.01)
        
        async def read():
            for _ in range(10):
                await store.load_async("order-600")
                await asyncio.sleep(0.005)
        
        # Run writers and readers concurrently
        await asyncio.gather(
            write(),
            write(),
            read(),
            read(),
            read(),
        )
        
        # Verify final state
        final = await store.load_async("order-600")
        assert len(final) == 11  # 1 initial + 2 writers * 5 events


@pytest.mark.asyncio
@pytest.mark.integration
class TestConnectionPool:
    """Test connection pooling behavior."""

    async def test_pool_handles_multiple_operations(self, store):
        """Test that pool efficiently handles many operations."""
        # Create many aggregates
        tasks = []
        for i in range(100):
            event = OrderCreated(
                order_id=f"order-{i}",
                customer_id=f"cust-{i}",
                amount=Decimal(str(i)),
            )
            tasks.append(store.save_async(f"pool-test-{i}", [event]))
        
        # All operations should complete without pool exhaustion
        await asyncio.gather(*tasks)
        
        # Verify all were saved
        loaded_tasks = [store.load_async(f"pool-test-{i}") for i in range(100)]
        results = await asyncio.gather(*loaded_tasks)
        
        assert all(len(events) == 1 for events in results)

    async def test_pool_recovery_after_errors(self, store):
        """Test that pool recovers after errors."""
        # Cause some errors
        for _ in range(5):
            try:
                # Try to save with invalid data
                await store.save_async("", [])  # Empty aggregate_id
            except:
                pass
        
        # Pool should still work for valid operations
        event = OrderCreated(
            order_id="recovery-test",
            customer_id="cust",
            amount=Decimal("100.00"),
        )
        await store.save_async("recovery", [event])
        
        loaded = await store.load_async("recovery")
        assert len(loaded) == 1


@pytest.mark.asyncio
@pytest.mark.integration
class TestPerformance:
    """Performance and scalability tests."""

    async def test_large_event_stream_performance(self, store):
        """Test performance with large event streams."""
        # Create 1000 events
        events = [
            OrderCreated(
                order_id=f"order-{i}",
                customer_id=f"cust-{i}",
                amount=Decimal(str(i)),
            )
            for i in range(1000)
        ]
        
        # Save in batches
        batch_size = 100
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            await store.save_async("large-stream", batch)
        
        # Load all events
        loaded = await store.load_async("large-stream")
        assert len(loaded) == 1000

    async def test_load_from_version(self, store):
        """Test loading events from specific version."""
        # Create 100 events
        events = [
            OrderCreated(
                order_id=f"order-{i}",
                customer_id=f"cust-{i}",
                amount=Decimal(str(i)),
            )
            for i in range(100)
        ]
        await store.save_async("version-test", events)
        
        # Load from version 50
        loaded = await store.load_async("version-test", from_version=50)
        assert len(loaded) == 49  # Events 51-99 (0-indexed)


@pytest.mark.asyncio
@pytest.mark.integration
class TestEdgeCases:
    """Edge cases and error conditions."""

    async def test_empty_events_list(self, store):
        """Test saving empty events list."""
        await store.save_async("empty-test", [])
        loaded = await store.load_async("empty-test")
        assert loaded == []

    async def test_special_characters_in_aggregate_id(self, store):
        """Test aggregate IDs with special characters."""
        special_ids = [
            "order-with-dashes",
            "order_with_underscores",
            "order.with.dots",
            "order:with:colons",
            "order/with/slashes",
        ]
        
        for agg_id in special_ids:
            event = OrderCreated(
                order_id=agg_id,
                customer_id="cust",
                amount=Decimal("100.00"),
            )
            await store.save_async(agg_id, [event])
            loaded = await store.load_async(agg_id)
            assert len(loaded) == 1

    async def test_very_long_aggregate_id(self, store):
        """Test very long aggregate IDs."""
        long_id = "order-" + "x" * 1000
        event = OrderCreated(
            order_id=long_id,
            customer_id="cust",
            amount=Decimal("100.00"),
        )
        await store.save_async(long_id, [event])
        loaded = await store.load_async(long_id)
        assert len(loaded) == 1

    async def test_unicode_in_event_data(self, store):
        """Test Unicode characters in event data."""
        event = OrderCreated(
            order_id="unicode-test",
            customer_id="客户-123-🎉",
            amount=Decimal("100.00"),
        )
        await store.save_async("unicode", [event])
        loaded = await store.load_async("unicode")
        assert loaded[0].data["customer_id"] == "客户-123-🎉"
