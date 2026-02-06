# Async API Design

**Status:** Implemented  
**Authors:** Stefan Poss

---

## Summary

Orchestrix provides full async/await support alongside its synchronous API. The async implementation is non-blocking and supports modern Python async frameworks like FastAPI, Starlette, and Quart.

---

## Goals

- First-class async support for all core abstractions
- Zero breaking changes — sync and async APIs coexist
- Concurrent handler execution via `asyncio.gather()`
- Full type safety with async/await
- No new external dependencies (uses `asyncio` stdlib)

---

## Async Message Bus

### Protocol

```python
from orchestrix.core.messaging.message_bus import AsyncMessageBus

class AsyncMessageBus(Protocol):
    async def publish(self, message: Message) -> None: ...
    def subscribe(
        self,
        message_type: type[T],
        handler: Callable[[T], Coroutine[Any, Any, None]],
    ) -> None: ...
```

### Implementation

```python
from orchestrix.infrastructure.memory.async_bus import InMemoryAsyncMessageBus
```

Key behavior: when `publish()` is called, **all handlers for that message type run concurrently** via `asyncio.gather()`. If any handler fails, a `HandlerError` is raised.

```python
bus = InMemoryAsyncMessageBus()

async def handle_order(event: OrderCreated) -> None:
    print(f"Processing {event.order_id}")

async def send_email(event: OrderCreated) -> None:
    print(f"Emailing for {event.order_id}")

bus.subscribe(OrderCreated, handle_order)
bus.subscribe(OrderCreated, send_email)

# Both handlers execute concurrently
await bus.publish(OrderCreated(order_id="ORD-001"))
```

---

## Async Event Store

### Protocol

```python
from orchestrix.core.eventsourcing.event_store import AsyncEventStore

class AsyncEventStore(Protocol):
    async def save(
        self,
        aggregate_id: str,
        events: Sequence[Event],
        expected_version: int | None = None,
    ) -> None: ...

    async def load(
        self,
        aggregate_id: str,
        from_version: int = 0,
    ) -> list[Event]: ...
```

### In-Memory Implementation

```python
from orchestrix.infrastructure.memory.async_store import InMemoryAsyncEventStore

store = InMemoryAsyncEventStore()
await store.save("ACC-001", [AccountOpened(...)], expected_version=0)
events = await store.load("ACC-001")
```

Supports snapshots via `save_snapshot()` / `load_snapshot()`.

### PostgreSQL Implementation

```python
from orchestrix.infrastructure.postgres.store import PostgreSQLEventStore

store = PostgreSQLEventStore(
    connection_string="postgresql://user:pass@localhost:5432/db",
    pool_min_size=5,
    pool_max_size=20,
)
await store.initialize()
```

`PostgreSQLEventStore` is inherently async (asyncpg connection pooling).

---

## Async Aggregate Repository

`AggregateRepository` provides both sync and async methods:

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRepository

repo = AggregateRepository(event_store=async_store)

# Async operations
account = await repo.load_async(BankAccount, "ACC-001")
account.deposit(500.0)
await repo.save_async(account)

# Sync operations (for sync event stores)
repo_sync = AggregateRepository(event_store=sync_store)
account = repo_sync.load(BankAccount, "ACC-001")
repo_sync.save(account)
```

---

## Async Command Handlers

Command handlers become async coroutines:

```python
class CreateOrderHandler:
    def __init__(self, bus: AsyncMessageBus, store: AsyncEventStore) -> None:
        self.bus = bus
        self.store = store

    async def handle(self, command: CreateOrder) -> None:
        order = Order(aggregate_id=command.order_id)
        order.create(command.customer_name)

        events = order.uncommitted_events
        await self.store.save(command.order_id, events)
        for event in events:
            await self.bus.publish(event)
        order.mark_events_committed()
```

---

## Async Sagas

`Saga` is async-native. Steps can be sync or async callables:

```python
from orchestrix.core.execution.saga import Saga, SagaStep, InMemorySagaStateStore

async def reserve_inventory(order_id: str) -> None: ...
async def release_inventory(order_id: str) -> None: ...

saga = Saga(
    saga_type="order-fulfillment",
    steps=[
        SagaStep("reserve", reserve_inventory, compensation=release_inventory),
        SagaStep("charge", charge_payment, compensation=refund_payment),
    ],
    state_store=InMemorySagaStateStore(),
)

await saga.initialize()
await saga.execute(order_id="ORD-001")
```

---

## Async Projections

`ProjectionEngine` is fully async:

```python
from orchestrix.core.eventsourcing.projection import (
    ProjectionEngine, InMemoryProjectionStateStore,
)

engine = ProjectionEngine("order-summary", InMemoryProjectionStateStore())

@engine.on(OrderCreated)
async def on_order(event: OrderCreated) -> None:
    totals[event.order_id] = event.total

await engine.initialize()
await engine.process_events(events)
```

---

## Migration Guide

### Sync to Async

| Sync | Async |
|------|-------|
| `InMemoryMessageBus` | `InMemoryAsyncMessageBus` |
| `InMemoryEventStore` | `InMemoryAsyncEventStore` |
| `bus.publish(msg)` | `await bus.publish(msg)` |
| `store.save(id, events)` | `await store.save(id, events)` |
| `repo.load(Type, id)` | `await repo.load_async(Type, id)` |
| `repo.save(agg)` | `await repo.save_async(agg)` |

Both APIs coexist — no breaking changes. Choose the variant that matches your context.

### FastAPI Integration Example

```python
from fastapi import FastAPI
from orchestrix.infrastructure.memory.async_bus import InMemoryAsyncMessageBus
from orchestrix.infrastructure.memory.async_store import InMemoryAsyncEventStore

app = FastAPI()
bus = InMemoryAsyncMessageBus()
store = InMemoryAsyncEventStore()

@app.post("/orders")
async def create_order(order_id: str, customer: str):
    await bus.publish(CreateOrder(order_id=order_id, customer_name=customer))
    return {"status": "accepted"}
```

---

## Performance

Async handlers for I/O-bound workloads see significant improvements:

| Approach | 100 messages × 5 handlers | Notes |
|----------|---------------------------|-------|
| Sync (sequential) | ~100ms | One at a time |
| Async (concurrent) | ~1ms | `asyncio.gather()` |

The advantage scales with handler I/O latency (network, database, file I/O).

---

## Next Steps

- [Architecture](../development/architecture.md) — System design overview
- [Infrastructure API](../api/infrastructure.md) — Async implementation details
- [Lakehouse Demo](../demos/lakehouse.md) — Full async FastAPI example
