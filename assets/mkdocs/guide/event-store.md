
# Event Store

Persist and replay event streams.

## Protocol

```python
class EventStore(Protocol):
    def save(self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None) -> None: ...
    def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]: ...

class AsyncEventStore(Protocol):
    async def save(self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None) -> None: ...
    async def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]: ...
```

## Implementations

### InMemoryEventStore

For development and testing:

```python
from orchestrix.infrastructure.memory.store import InMemoryEventStore

store = InMemoryEventStore()
store.save("order-123", [event1, event2])
events = store.load("order-123")
```

Also supports snapshots:

```python
from orchestrix.core.eventsourcing.snapshot import Snapshot

snapshot = Snapshot(aggregate_id="order-123", aggregate_type="Order", version=5, state={...})
store.save_snapshot(snapshot)
loaded = store.load_snapshot("order-123")
```

And trace-based loading:

```python
events = store.load_by_trace(trace_id="abc-123")
```

### InMemoryAsyncEventStore

```python
from orchestrix.infrastructure.memory.async_store import InMemoryAsyncEventStore

store = InMemoryAsyncEventStore()
await store.save("order-123", [event1])
events = await store.load("order-123")
```

### PostgreSQLEventStore

Production-grade store using `asyncpg`:

```python
from orchestrix.infrastructure.postgres.store import PostgreSQLEventStore

store = PostgreSQLEventStore(
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    pool_min_size=10,
    pool_max_size=50,
    pool_timeout=30.0,
)
await store.initialize()  # creates schema + connection pool

await store.save("order-123", [event1], expected_version=0)
events = await store.load("order-123")

await store.close()
```

### GCP Stores

```python
from orchestrix.infrastructure.gcp_cloud_sql import GCPCloudSQLEventStore
from orchestrix.infrastructure.gcp_bigquery import GCPBigQueryEventStore
```

## Optimistic Concurrency

Pass `expected_version` to prevent concurrent write conflicts:

```python
store.save("order-123", new_events, expected_version=5)
# Raises ConcurrencyError if current version != 5
```

```python
from orchestrix.core.common.exceptions import ConcurrencyError

try:
    store.save("order-123", events, expected_version=5)
except ConcurrencyError as e:
    print(f"Conflict: expected v{e.expected_version}, got v{e.actual_version}")
```

## Snapshots

For aggregates with many events, use snapshots to speed up loading:

```python
# Save snapshot every N events
if aggregate.version % 100 == 0:
    snapshot = Snapshot(
        aggregate_id=aggregate.aggregate_id,
        aggregate_type="Order",
        version=aggregate.version,
        state={"status": aggregate.status, "total": aggregate.total},
    )
    store.save_snapshot(snapshot)

# Load with snapshot
snapshot = store.load_snapshot("order-123")
if snapshot:
    # Restore state from snapshot, then replay only newer events
    events = store.load("order-123", from_version=snapshot.version + 1)
```

## Comparison

| Store | Use Case | Async | Snapshots | Concurrency |
|---|---|---|---|---|
| `InMemoryEventStore` | Dev/test | Sync | ✅ | ✅ |
| `InMemoryAsyncEventStore` | Async dev | Async | ✅ | ✅ |
| `PostgreSQLEventStore` | Production | Async | ✅ | ✅ |
| `GCPCloudSQLEventStore` | GCP | Async | ❌ | ✅ |
| `GCPBigQueryEventStore` | Analytics | Async | ❌ | ❌ |
