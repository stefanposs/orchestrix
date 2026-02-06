
# Core Concepts

Orchestrix implements **Domain-Driven Design (DDD)**, **Event Sourcing**, and
**CQRS** patterns. This page covers the building blocks.

## Messages

All communication uses **Messages** — immutable, CloudEvents-compatible dataclasses:

```python
from orchestrix.core.messaging.message import Message, Command, Event
```

Every message has auto-generated fields: `id`, `type`, `source`, `timestamp`,
`correlation_id`, `causation_id`, `trace_id`.

## Commands

**Commands** = intentions. Imperative naming. Handled by exactly one handler.

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Command

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_name: str
    total_amount: float
```

## Events

**Events** = facts. Past-tense naming. Handled by zero or more handlers.

```python
from orchestrix.core.messaging.message import Event

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str
    total_amount: float
```

## Aggregates

**Aggregates** enforce business rules and emit events. State is rebuilt from events.

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRoot

@dataclass
class Order(AggregateRoot):
    customer_name: str = ""
    total_amount: float = 0.0
    status: str = "pending"

    def create(self, cmd):
        self._apply_event(OrderCreated(...))

    def _when_order_created(self, event: OrderCreated):
        self.aggregate_id = event.order_id
        self.customer_name = event.customer_name
        self.total_amount = event.total_amount
```

Key methods on `AggregateRoot`:

| Method | Purpose |
|---|---|
| `_apply_event(event)` | Record event and apply state change |
| `_when_<snake_case>(event)` | Convention-based state mutator |
| `mark_events_committed()` | Clear pending events after save |

## AggregateRepository

Loads and saves aggregates via an event store:

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore

store = InMemoryEventStore()
repo = AggregateRepository(event_store=store)

# Save
repo.save(order_aggregate)

# Load (replays events to rebuild state)
order = repo.load(Order, "order-123")

# Async variants
await repo.save_async(order)
order = await repo.load_async(Order, "order-123")
```

## Message Bus

Routes messages to handlers:

```python
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus

bus = InMemoryMessageBus()
bus.subscribe(CreateOrder, handle_create_order)
bus.subscribe(OrderCreated, send_confirmation_email)
bus.publish(CreateOrder(...))
```

Async variant: `InMemoryAsyncMessageBus` with `await bus.publish(...)`.

## Event Store

Persists event streams. Protocol with `save()` and `load()`:

```python
from orchestrix.infrastructure.memory.store import InMemoryEventStore

store = InMemoryEventStore()
store.save("order-123", [event1, event2], expected_version=0)
events = store.load("order-123")
```

Implementations:

| Store | Use Case |
|---|---|
| `InMemoryEventStore` | Development, testing |
| `InMemoryAsyncEventStore` | Async development |
| `PostgreSQLEventStore` | Production (asyncpg) |
| `GCPCloudSQLEventStore` | Google Cloud SQL |
| `GCPBigQueryEventStore` | Analytics workloads |

## Modules

Encapsulate domain logic and wire handlers:

```python
from orchestrix.core.common.module import Module

class OrderModule:
    def register(self, bus, store):
        bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
        bus.subscribe(OrderCreated, log_order)
```

## Flow

```
Application → Command → MessageBus → CommandHandler → Aggregate → Events
                                                                    ↓
                                                              EventStore
                                                                    ↓
                                                        Event Handlers (projections, side-effects)
```

## Next Steps

- [User Guide](../guide/index.md) — Production patterns
- [Demos](../demos/index.md) — Working examples
