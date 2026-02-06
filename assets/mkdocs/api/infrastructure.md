# Infrastructure API Reference

Concrete implementations of the core Protocols. All imports use the full module path.

---

## In-Memory Implementations

### `InMemoryMessageBus`

Synchronous in-memory message bus. Handlers called in subscription order.

```python
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus
```

```python
class InMemoryMessageBus:
    def __init__(self) -> None: ...
    def publish(self, message: Message) -> None: ...
    def subscribe(self, message_type: type[T], handler: Callable[[T], None]) -> None: ...
```

**Characteristics:**

- Synchronous handler execution in subscription order
- If a handler raises, subsequent handlers are **not** called
- No persistence between restarts
- Not thread-safe

**Example:**

```python
bus = InMemoryMessageBus()
bus.subscribe(OrderCreated, lambda e: print(f"Order {e.order_id} created"))
bus.publish(OrderCreated(order_id="ORD-001"))
```

### `InMemoryAsyncMessageBus`

Async message bus. Handlers execute **concurrently** via `asyncio.gather()`.

```python
from orchestrix.infrastructure.memory.async_bus import InMemoryAsyncMessageBus
```

```python
class InMemoryAsyncMessageBus:
    def __init__(self) -> None: ...
    async def publish(self, message: Message) -> None: ...
    def subscribe(self, message_type: type[T], handler: Callable[[T], Coroutine]) -> None: ...
```

**Example:**

```python
bus = InMemoryAsyncMessageBus()

async def handle_order(event: OrderCreated) -> None:
    print(f"Order {event.order_id} created")

bus.subscribe(OrderCreated, handle_order)
await bus.publish(OrderCreated(order_id="ORD-001"))
```

### `InMemoryEventStore`

Synchronous in-memory event store with optimistic locking and snapshot support.

```python
from orchestrix.infrastructure.memory.store import InMemoryEventStore
```

```python
class InMemoryEventStore:
    def __init__(self) -> None: ...
    def save(self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None) -> None: ...
    def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]: ...
    def load_by_trace(self, trace_id: str) -> list[Event]: ...
    def save_snapshot(self, snapshot: Snapshot) -> None: ...
    def load_snapshot(self, aggregate_id: str) -> Snapshot | None: ...
```

**Key behaviors:**

- Append-only semantics — `save()` appends, never replaces
- `load()` returns events in chronological order
- `load("UNKNOWN")` returns `[]` (empty list, not error)
- `expected_version` enables optimistic locking (raises `ConcurrencyError` on conflict)
- `load_by_trace(trace_id)` finds events across all aggregates by trace ID

**Example:**

```python
store = InMemoryEventStore()

# Save events
store.save("ORD-001", [OrderCreated(order_id="ORD-001")])
store.save("ORD-001", [OrderPaid(order_id="ORD-001")])

# Load returns both
events = store.load("ORD-001")
# → [OrderCreated, OrderPaid]

# Optimistic locking
store.save("ORD-001", [OrderShipped(...)], expected_version=2)
```

### `InMemoryAsyncEventStore`

Async variant with snapshot support.

```python
from orchestrix.infrastructure.memory.async_store import InMemoryAsyncEventStore
```

```python
class InMemoryAsyncEventStore:
    def __init__(self) -> None: ...
    async def save(self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None) -> None: ...
    async def load(self, aggregate_id: str, from_version: int = 0) -> list[Event]: ...
    async def save_snapshot(self, snapshot: Snapshot) -> None: ...
    async def load_snapshot(self, aggregate_id: str) -> Snapshot | None: ...
```

---

## PostgreSQL Event Store

Production-grade event store with connection pooling and async support.

```python
from orchestrix.infrastructure.postgres.store import PostgreSQLEventStore
```

```python
@dataclass(frozen=True)
class PostgreSQLEventStore:
    connection_string: str
    pool_min_size: int = 10
    pool_max_size: int = 50
    pool_timeout: float = 30.0
```

| Method | Signature |
|--------|-----------|
| `initialize` | `async () -> None` — Create pool, ensure schema |
| `close` | `async () -> None` — Release pool |
| `save` | `async (aggregate_id, events, expected_version=None) -> None` |
| `load` | `async (aggregate_id, from_version=None) -> list[Event]` |
| `save_snapshot_async` | `async (snapshot: Snapshot) -> None` |
| `load_snapshot_async` | `async (aggregate_id: str) -> Snapshot \| None` |
| `ping` | `async () -> bool` — Health check |

!!! warning
    The sync `save_snapshot()` and `load_snapshot()` methods raise `NotImplementedError`. Use the `_async` variants.

**Example:**

```python
store = PostgreSQLEventStore(
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    pool_min_size=5,
    pool_max_size=20,
)
await store.initialize()

try:
    await store.save("ACC-001", [AccountOpened(...)], expected_version=0)
    events = await store.load("ACC-001")
finally:
    await store.close()
```

**Features:**

- Automatic connection pooling (asyncpg)
- Auto-creates `events` and `snapshots` tables on `initialize()`
- JSON serialization with `OrchestrixJSONEncoder` (handles Decimal, datetime, UUID, dataclasses)
- Optimistic locking via `expected_version`
- Snapshot support for fast aggregate hydration

---

## Observability — Jaeger Tracing

Distributed tracing using OpenTelemetry with Jaeger backend.

```python
from orchestrix.infrastructure.observability.jaeger import (
    JaegerTracer, TracingConfig, init_tracing, get_tracer,
)
```

### `TracingConfig`

```python
@dataclass(frozen=True)
class TracingConfig:
    service_name: str
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    jaeger_sampler_type: str = "const"
    jaeger_sampler_param: float = 1.0
```

### `JaegerTracer`

```python
class JaegerTracer:
    def __init__(self, tracer_name: str = "orchestrix") -> None: ...
```

**Context-manager spans:**

| Method | Purpose |
|--------|---------|
| `span(operation_name, attributes=None)` | General-purpose span (sync) |
| `async_span(operation_name, attributes=None)` | General-purpose span (async) |
| `span_event(event_type, event_id, aggregate_id)` | Event processing span (sync) |
| `async_span_event(...)` | Event processing span (async) |
| `span_command(command_type, aggregate_id)` | Command handling span (sync) |
| `async_span_command(...)` | Command handling span (async) |
| `span_saga(saga_type, saga_id)` | Saga execution span (sync) |
| `async_span_saga(...)` | Saga execution span (async) |

**Utility methods:** `get_trace_id()`, `set_attribute(key, value)`, `add_event(name, attributes)`

**Example:**

```python
tracer = init_tracing(service_name="my-service")

with tracer.span_command("CreateOrder", "ORD-001"):
    # … handle command
    with tracer.span_event("OrderCreated", event.id, "ORD-001"):
        store.save("ORD-001", [event])
```

---

## Observability — Prometheus Metrics

Prometheus metrics provider for event sourcing systems.

```python
from orchestrix.infrastructure.observability.prometheus import (
    PrometheusMetrics, MetricConfig, MetricOperationType,
)
```

### `MetricConfig`

```python
@dataclass(frozen=True)
class MetricConfig:
    namespace: str = "orchestrix"
    subsystem: str = "core"
    registry: CollectorRegistry | None = None
    enable_summary_metrics: bool = True
```

### `PrometheusMetrics`

```python
class PrometheusMetrics:
    def __init__(self, config: MetricConfig | None = None) -> None: ...
```

**Context-manager trackers:**

| Method | Purpose |
|--------|---------|
| `track_event_publish(event_type)` | Measure event publish duration |
| `track_command_handle(command_type)` | Measure command handling duration |
| `track_aggregate_load(aggregate_type)` | Measure aggregate load duration |
| `track_storage_operation(operation_type)` | Measure storage operation duration |
| `track_projection_update(projection_name)` | Measure projection update duration |
| `track_saga_execution(saga_type)` | Measure saga execution duration |
| `track_async_event_publish(event_type)` | Async event publish |
| `track_async_command_handle(command_type)` | Async command handling |

**Other methods:**

| Method | Signature |
|--------|-----------|
| `record_projection_lag` | `(projection_name: str, events_behind: int) -> None` |
| `get_prometheus_registry` | `() -> CollectorRegistry` |
| `generate_exposition` | `(registry) -> bytes` (static) |

**Registered instruments:** `events_total`, `events_processing_seconds`, `commands_total`, `commands_latency_seconds`, `aggregates_loaded_total`, `aggregates_load_time_seconds`, `aggregates_in_memory`, `storage_operations_total`, `storage_operation_seconds`, `projection_events_behind`, `projection_update_seconds`, `saga_executions_total`, `saga_duration_seconds`

**Example:**

```python
metrics = PrometheusMetrics(MetricConfig(namespace="myapp"))

with metrics.track_command_handle("CreateOrder"):
    handle_create_order(command)

with metrics.track_storage_operation(MetricOperationType.APPEND):
    store.save(aggregate_id, events)
```

### Exposing `/metrics` endpoint

```python
from prometheus_client import generate_latest

@app.get("/metrics")
def metrics():
    registry = metrics_provider.get_prometheus_registry()
    return Response(generate_latest(registry), media_type="text/plain")
```

---

## Implementation Comparison

| Feature | InMemory | PostgreSQL |
|---------|----------|------------|
| Persistence | No | Yes |
| Async | Both | Async only |
| Optimistic locking | Yes | Yes |
| Snapshots | Yes | Yes (async) |
| Connection pooling | N/A | Yes (asyncpg) |
| Thread-safe | No | Yes |
| Use case | Dev / Test | Production |

---

## Next Steps

- [Core API](core.md) — Protocol definitions
- [Event Store Guide](../guide/event-store.md) — Patterns and migration
- [Production Deployment](../guide/production-deployment.md) — Scaling guidance
