# Core API Reference

Complete reference for all core abstractions in Orchestrix.

---

## Messages

All messages are **immutable frozen dataclasses** with CloudEvents-compatible metadata.

### `Message`

```python
from orchestrix.core.messaging.message import Message
```

```python
@dataclass(frozen=True, kw_only=True)
class Message:
    id: str                          # UUID (auto-generated)
    specversion: str = "1.0"         # CloudEvents spec version
    type: str = ""                   # Auto-derived from class name
    source: str = "orchestrix"       # Message origin
    timestamp: datetime              # UTC (auto-generated)
    subject: str | None = None       # Optional subject
    data: Any = None                 # Optional payload
    datacontenttype: str | None = None
    dataschema: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    trace_id: str | None = None
```

**Example — Custom event with domain fields:**

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Event

@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str
```

### `Command`

Represents an **intent** to change state. Handled by a `CommandHandler`.

```python
@dataclass(frozen=True)
class Command(Message): ...
```

### `Event`

Represents a **fact** that has occurred. Immutable record of a state change.

```python
@dataclass(frozen=True)
class Event(Message): ...
```

---

## Message Bus

### `MessageBus` (Protocol)

Synchronous message bus for command and event routing.

```python
from orchestrix.core.messaging.message_bus import MessageBus
```

| Method | Signature |
|--------|-----------|
| `publish` | `(message: Message) -> None` |
| `subscribe` | `(message_type: type[T], handler: Callable[[T], None]) -> None` |

### `AsyncMessageBus` (Protocol)

Asynchronous variant — handlers execute concurrently via `asyncio.gather()`.

```python
from orchestrix.core.messaging.message_bus import AsyncMessageBus
```

| Method | Signature |
|--------|-----------|
| `publish` | `async (message: Message) -> None` |
| `subscribe` | `(message_type: type[T], handler: Callable[[T], Coroutine]) -> None` |

---

## Command Handler

### `CommandHandler` (Protocol)

```python
from orchestrix.core.messaging.command_handler import CommandHandler
```

```python
class CommandHandler(Protocol):
    def __init__(self, bus: MessageBus, store: EventStore): ...
    def handle(self, command: Command) -> None: ...
    def _persist_and_publish(self, aggregate_id: str, events: list[Event]) -> None: ...
```

!!! note
    `CommandHandler` is a **Protocol**, not a generic class. Implement it by matching the method signatures — no inheritance required.

**Example:**

```python
class CreateUserHandler:
    def __init__(self, bus: MessageBus, store: EventStore) -> None:
        self.bus = bus
        self.store = store

    def handle(self, command: CreateUser) -> None:
        user = UserAggregate(aggregate_id=command.user_id)
        user._apply_event(UserCreated(user_id=command.user_id, email=command.email))
        self.store.save(command.user_id, user.uncommitted_events)
        for event in user.uncommitted_events:
            self.bus.publish(event)
        user.mark_events_committed()
```

---

## Event Store

### `EventStore` (Protocol)

Synchronous event store with optimistic locking.

```python
from orchestrix.core.eventsourcing.event_store import EventStore
```

| Method | Signature |
|--------|-----------|
| `save` | `(aggregate_id: str, events: Sequence[Event], expected_version: int \| None = None) -> None` |
| `load` | `(aggregate_id: str, from_version: int = 0) -> list[Event]` |

### `AsyncEventStore` (Protocol)

Asynchronous variant with the same interface.

```python
from orchestrix.core.eventsourcing.event_store import AsyncEventStore
```

| Method | Signature |
|--------|-----------|
| `save` | `async (aggregate_id: str, events: Sequence[Event], expected_version: int \| None = None) -> None` |
| `load` | `async (aggregate_id: str, from_version: int = 0) -> list[Event]` |

**`expected_version`** enables optimistic locking: if the current stream version doesn't match, a `ConcurrencyError` is raised.

---

## Aggregates

### `AggregateRoot`

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRoot
```

```python
@dataclass
class AggregateRoot:
    aggregate_id: str = ""
    version: int = 0
    uncommitted_events: list[Event]  # (init=False)
```

| Method | Purpose |
|--------|---------|
| `_apply_event(event)` | Apply event, track in `uncommitted_events`, increment `version` |
| `_when(event)` | Routes to `_when_{snake_case_type}(event)` method |
| `mark_events_committed()` | Clear `uncommitted_events` after persistence |
| `_replay_events(events)` | Rebuild aggregate state from event history |

**Example — Domain aggregate:**

```python
from dataclasses import dataclass
from orchestrix.core.eventsourcing.aggregate import AggregateRoot

@dataclass
class BankAccount(AggregateRoot):
    balance: float = 0.0
    owner: str = ""

    def open(self, owner: str, initial_deposit: float) -> None:
        self._apply_event(AccountOpened(
            account_id=self.aggregate_id,
            owner=owner,
            initial_deposit=initial_deposit,
        ))

    def _when_account_opened(self, event: AccountOpened) -> None:
        self.owner = event.owner
        self.balance = event.initial_deposit
```

### `AggregateRepository`

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRepository
```

```python
@dataclass
class AggregateRepository[T: AggregateRoot]:
    event_store: EventStore | AsyncEventStore
```

| Method | Signature |
|--------|-----------|
| `load` | `(aggregate_type: type[T], aggregate_id: str) -> T` |
| `save` | `(aggregate: T) -> None` |
| `load_async` | `async (aggregate_type: type[T], aggregate_id: str) -> T` |
| `save_async` | `async (aggregate: T) -> None` |

**Example:**

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore

store = InMemoryEventStore()
repo = AggregateRepository(event_store=store)

# Save
account = BankAccount(aggregate_id="ACC-001")
account.open("Alice", 1000.0)
repo.save(account)

# Load
loaded = repo.load(BankAccount, "ACC-001")
assert loaded.balance == 1000.0
```

---

## Projections

### `ProjectionEngine`

Build CQRS read models from event streams.

```python
from orchestrix.core.eventsourcing.projection import (
    ProjectionEngine,
    InMemoryProjectionStateStore,
)
```

```python
class ProjectionEngine:
    def __init__(
        self,
        projection_id: str,
        state_store: ProjectionStateStore,
        tracing: TracingProvider | None = None,
    ): ...
```

| Method | Purpose |
|--------|---------|
| `on(event_type)` | Decorator to register an event handler |
| `handle_event(event)` | Process a single event (async) |
| `process_events(events)` | Process a batch of events (async) |
| `replay(events)` | Reset and replay from scratch (async) |
| `get_state()` | Return current `ProjectionState` |
| `is_healthy()` | Health check |

**Example:**

```python
state_store = InMemoryProjectionStateStore()
engine = ProjectionEngine("order-summary", state_store)

order_totals: dict[str, float] = {}

@engine.on(OrderCreated)
async def on_order_created(event: OrderCreated) -> None:
    order_totals[event.order_id] = event.total_amount

await engine.initialize()
await engine.process_events(events)
```

### `ProjectionState`

```python
@dataclass(frozen=True, kw_only=True)
class ProjectionState:
    projection_id: str
    last_processed_event_id: str | None = None
    last_processed_position: int = 0
    updated_at: datetime
    error_count: int = 0
    is_healthy: bool = True
```

---

## Sagas

### `Saga`

Orchestrate long-running business processes with compensation logic.

```python
from orchestrix.core.execution.saga import (
    Saga, SagaStep, SagaState, SagaStatus,
    InMemorySagaStateStore,
)
```

```python
class Saga:
    def __init__(
        self,
        saga_type: str,
        steps: list[SagaStep],
        state_store: SagaStateStore,
        tracing: TracingProvider | None = None,
    ): ...
```

| Method | Purpose |
|--------|---------|
| `initialize()` | Create initial saga state (async) |
| `execute(**kwargs)` | Run all steps; compensate on failure (async) |
| `get_state()` | Return current `SagaState` |
| `is_completed()` | Check if saga finished |
| `is_successful()` | Check if saga completed without error |

### `SagaStep`

```python
@dataclass
class SagaStep:
    name: str
    action: Callable[..., Any]
    compensation: Callable[..., Any] | None = None
```

### `SagaStatus` (Enum)

`PENDING` · `IN_PROGRESS` · `COMPLETED` · `COMPENSATING` · `FAILED`

**Example:**

```python
state_store = InMemorySagaStateStore()

saga = Saga(
    saga_type="order-fulfillment",
    steps=[
        SagaStep(
            name="reserve_inventory",
            action=reserve_inventory,
            compensation=release_inventory,
        ),
        SagaStep(
            name="charge_payment",
            action=charge_payment,
            compensation=refund_payment,
        ),
        SagaStep(name="ship_order", action=ship_order),
    ],
    state_store=state_store,
)

await saga.initialize()
await saga.execute(order_id="ORD-001", amount=99.99)
assert saga.is_successful()
```

---

## Event Versioning

### `EventUpcaster`

Transform events between schema versions.

```python
from orchestrix.core.eventsourcing.versioning import (
    EventUpcaster, UpcasterRegistry, VersionedEvent,
)
```

```python
class EventUpcaster[SourceEvent, TargetEvent]:
    def __init__(self, source_version: int, target_version: int): ...
    async def upcast(self, event: Event) -> TargetEvent: ...  # abstract
    async def can_upcast(self, event: Event) -> bool: ...
```

### `UpcasterRegistry`

```python
class UpcasterRegistry:
    def register(self, event_type: str, upcaster: EventUpcast) -> None: ...
    def get_upcaster(self, event_type: str, source_version: int, target_version: int) -> EventUpcast | None: ...
    async def upcast(self, event: Event, event_type: str, target_version: int) -> Event: ...
    def get_chain_info(self, event_type: str) -> list[tuple[int, int]]: ...
```

### `VersionedEvent`

```python
@dataclass(frozen=True)
class VersionedEvent:
    event: Event
    version: int
    event_type: str
```

---

## Validation

```python
from orchestrix.core.common.validation import (
    ValidationError,
    validate_not_empty,
    validate_positive,
    validate_non_negative,
    validate_min_length,
    validate_max_length,
    validate_in_range,
    validate_one_of,
)
```

| Function | Signature |
|----------|-----------|
| `validate_not_empty` | `(value: str, field: str) -> None` |
| `validate_positive` | `(value: float \| int, field: str) -> None` |
| `validate_non_negative` | `(value: float \| int, field: str) -> None` |
| `validate_min_length` | `(value: str, min_length: int, field: str) -> None` |
| `validate_max_length` | `(value: str, max_length: int, field: str) -> None` |
| `validate_in_range` | `(value: float \| int, min_value, max_value, field: str) -> None` |
| `validate_one_of` | `(value: object, allowed_values: Sequence, field: str) -> None` |

All raise `ValidationError` on failure.

**Example:**

```python
from orchestrix.core.common.validation import validate_not_empty, validate_positive

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    amount: float

    def __post_init__(self) -> None:
        validate_not_empty(self.order_id, "order_id")
        validate_positive(self.amount, "amount")
```

---

## Retry Policies

```python
from orchestrix.core.common.retry import (
    RetryPolicy, ExponentialBackoff, LinearBackoff, FixedDelay, NoRetry,
    retry_sync,
)
```

| Class | Constructor |
|-------|-------------|
| `ExponentialBackoff` | `(max_retries=3, initial_delay=1.0, max_delay=60.0, multiplier=2.0, jitter=True)` |
| `LinearBackoff` | `(max_retries=3, initial_delay=1.0, increment=1.0, max_delay=60.0)` |
| `FixedDelay` | `(max_retries=3, delay=1.0)` |
| `NoRetry` | `()` |

All implement `RetryPolicy`:

```python
class RetryPolicy(ABC):
    def should_retry(self, attempt: int) -> bool: ...
    def get_delay(self, attempt: int) -> float: ...
```

**Helper function:**

```python
retry_sync(func, *args, policy=ExponentialBackoff(), **kwargs)
```

---

## Module

### `Module` (Protocol)

```python
from orchestrix.core.common.module import Module
```

```python
class Module(Protocol):
    def register(self, bus: MessageBus, store: EventStore) -> None: ...
```

---

## Observability

### `ObservabilityHooks`

```python
from orchestrix.core.common.observability import (
    ObservabilityHooks, init_observability, get_observability,
    MetricsProvider, TracingProvider, NoOpMetricsProvider, NoOpTracingProvider,
    MetricValue, TraceSpan,
)
```

```python
class ObservabilityHooks:
    def __init__(
        self,
        metrics_provider: MetricsProvider | None = None,
        tracing_provider: TracingProvider | None = None,
        logger: logging.Logger | None = None,
    ): ...
```

**Event tracking methods:**

| Method | Signature |
|--------|-----------|
| `record_event_stored` | `(aggregate_id: str, version: int) -> None` |
| `record_event_loaded` | `(aggregate_id: str, count: int) -> None` |
| `record_event_replayed` | `(aggregate_id: str, event_type: str) -> None` |
| `record_snapshot_saved` | `(aggregate_id: str, version: int) -> None` |
| `record_snapshot_loaded` | `(aggregate_id: str, version: int) -> None` |
| `record_aggregate_error` | `(aggregate_id: str, error: str) -> None` |
| `start_event_store_operation` | `(operation: str) -> TraceSpan` |

**Hook registration:** `on_event_stored`, `on_event_loaded`, `on_event_replayed`, `on_snapshot_saved`, `on_snapshot_loaded`, `on_aggregate_error`

### `MetricsProvider` (ABC)

```python
class MetricsProvider(ABC):
    def record_metric(self, metric: MetricValue) -> None: ...
    def counter(self, name: str, value: float = 1.0, labels: dict | None = None) -> None: ...
    def gauge(self, name: str, value: float, labels: dict | None = None) -> None: ...
    def histogram(self, name: str, value: float, unit: str = "", labels: dict | None = None) -> None: ...
```

### `TracingProvider` (ABC)

```python
class TracingProvider(ABC):
    def start_span(self, operation: str) -> TraceSpan: ...
    def end_span(self, span: TraceSpan) -> None: ...
```

---

## Logging

```python
from orchestrix.core.common.logging import get_logger, StructuredLogger
```

```python
def get_logger(name: str) -> logging.Logger: ...

class StructuredLogger:
    def __init__(self, logger: logging.Logger): ...
    def info(self, message: str, **context) -> None: ...
    def error(self, message: str, **context) -> None: ...
    def warning(self, message: str, **context) -> None: ...
    def debug(self, message: str, **context) -> None: ...
    def exception(self, message: str, **context) -> None: ...
```

---

## Exceptions

```python
from orchestrix.core.common.exceptions import (
    OrchestrixError, HandlerError, ConcurrencyError,
)
```

| Exception | Fields |
|-----------|--------|
| `OrchestrixError` | Base class for all framework errors |
| `HandlerError` | `message_type: str`, `handler_name: str`, `original_error: Exception` |
| `ConcurrencyError` | `aggregate_id: str`, `expected_version: int`, `actual_version: int` |

---

## Snapshot

```python
from orchestrix.core.eventsourcing.snapshot import Snapshot
```

```python
@dataclass(frozen=True)
class Snapshot:
    aggregate_id: str
    aggregate_type: str
    version: int
    state: dict[str, Any]
    timestamp: datetime  # auto-generated
```

Used by `InMemoryEventStore.save_snapshot()` / `load_snapshot()` and `PostgreSQLEventStore.save_snapshot_async()` / `load_snapshot_async()`.

---

## Next Steps

- [Infrastructure API](infrastructure.md) — Concrete implementations
- [Quick Start](../getting-started/quick-start.md) — Build your first system
- [Best Practices](../guide/best-practices.md) — Production patterns
