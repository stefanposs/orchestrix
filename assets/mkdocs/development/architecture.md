# Architecture

Technical architecture and design decisions behind Orchestrix.

---

## Core Principles

### 1. Protocol-Based Design

Orchestrix uses `typing.Protocol` instead of Abstract Base Classes for all core interfaces:

```python
class MessageBus(Protocol):
    def publish(self, message: Message) -> None: ...
    def subscribe(self, message_type: type[T], handler: Callable[[T], None]) -> None: ...
```

**Advantages:**

- Duck typing — Pythonic, no inheritance required
- Better IDE autocompletion and type checking
- Easy to mock in tests — any matching object works
- Clear, minimal contracts

### 2. Immutable Messages

All messages are `frozen` dataclasses with CloudEvents metadata:

```python
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str
    # Inherited: id, specversion, type, source, timestamp,
    #            correlation_id, causation_id, trace_id, …
```

- Thread-safe and hashable
- Prevents unexpected mutations after creation
- CloudEvents-compatible for interoperability

### 3. Event Sourcing First

Events are the single source of truth. Aggregate state is reconstructed by replaying events:

```python
account = AggregateRepository(event_store=store).load(BankAccount, "ACC-001")
# Internally: events = store.load("ACC-001") → replay → BankAccount instance
```

- Complete audit trail
- Time travel (state at any historical point)
- Event replay for projections and analytics
- Built-in debugging through event history

---

## Architecture Layers

```
┌─────────────────────────────────────────────┐
│           Application Layer                 │
│  (Modules, Use Cases, Wiring)               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Domain Layer                      │
│  (AggregateRoot, Commands, Events, Sagas)   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Infrastructure Layer                │
│  (MessageBus, EventStore, Observability)    │
└─────────────────────────────────────────────┘
```

### Application Layer

`Module` implementations wire domain logic to infrastructure:

```python
from orchestrix.core.common.module import Module

class OrderModule:
    def register(self, bus: MessageBus, store: EventStore) -> None:
        handler = CreateOrderHandler(bus, store)
        bus.subscribe(CreateOrder, handler.handle)
        bus.subscribe(OrderCreated, send_confirmation_email)
```

### Domain Layer

Business rules live in `AggregateRoot` subclasses:

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRoot

@dataclass
class Order(AggregateRoot):
    status: str = "pending"

    def cancel(self) -> None:
        if self.status == "shipped":
            raise ValueError("Cannot cancel shipped order")
        self._apply_event(OrderCancelled(order_id=self.aggregate_id))

    def _when_order_cancelled(self, event: OrderCancelled) -> None:
        self.status = "cancelled"
```

### Infrastructure Layer

Pluggable implementations of core Protocols:

| Component | Dev / Test | Production |
|-----------|-----------|------------|
| MessageBus | `InMemoryMessageBus` | `InMemoryMessageBus` / custom |
| AsyncMessageBus | `InMemoryAsyncMessageBus` | `InMemoryAsyncMessageBus` / custom |
| EventStore | `InMemoryEventStore` | `PostgreSQLEventStore` |
| Metrics | `NoOpMetricsProvider` | `PrometheusMetrics` |
| Tracing | `NoOpTracingProvider` | `JaegerTracer` |

---

## Polylith Repository Structure

Orchestrix uses the [Polylith](https://polylith.gitbook.io/) architecture for modular monorepo layout:

```
orchestrix/
├── components/orchestrix/     # Reusable building blocks
│   ├── core/                  # Domain Protocols & base classes
│   │   ├── messaging/         # Message, Command, Event, MessageBus, CommandHandler
│   │   ├── eventsourcing/     # AggregateRoot, EventStore, Projection, Versioning
│   │   ├── execution/         # Saga
│   │   └── common/            # Module, Validation, Retry, Observability, Logging
│   └── infrastructure/        # Concrete implementations
│       ├── memory/            # InMemoryMessageBus, InMemoryEventStore, async variants
│       ├── postgres/          # PostgreSQLEventStore
│       └── observability/     # JaegerTracer, PrometheusMetrics
├── bases/orchestrix/          # Application entry points (demos)
│   ├── banking_demo/
│   ├── ecommerce_demo/
│   ├── lakehouse_fastapi_demo/
│   └── …
├── projects/                  # Deployable artifacts (pyproject.toml per project)
│   ├── orchestrix_lib/        # The published library package
│   ├── banking_demo/
│   └── …
└── test/                      # All tests
    ├── conftest.py            # Shared fixtures (bus, store)
    ├── components/orchestrix/
    │   ├── core/              # Unit tests for core modules
    │   └── infrastructure/    # Integration tests for implementations
    ├── benchmarks/            # Performance benchmarks
    └── projects/              # Project-level integration tests
```

**Key rule:** Components never import from bases or projects. Bases compose components. Projects wire everything together.

---

## Design Patterns

### Command Pattern

Commands encapsulate requests; handlers execute them:

```python
bus.publish(CreateOrder(order_id="ORD-001", customer_id="CUST-123"))
# → routed to CreateOrderHandler.handle()
```

### Observer Pattern

`MessageBus.subscribe()` implements observer — multiple handlers per event type:

```python
bus.subscribe(OrderCreated, send_email)
bus.subscribe(OrderCreated, update_inventory)
bus.subscribe(OrderCreated, record_analytics)
```

### Repository Pattern

`AggregateRepository` abstracts event persistence:

```python
repo = AggregateRepository(event_store=store)
account = repo.load(BankAccount, "ACC-001")
account.deposit(500.0)
repo.save(account)
```

### Saga Pattern

`Saga` orchestrates multi-step processes with compensation:

```python
saga = Saga(saga_type="order-fulfillment", steps=[
    SagaStep("reserve", reserve_inventory, compensation=release_inventory),
    SagaStep("charge", charge_payment, compensation=refund_payment),
    SagaStep("ship", ship_order),
], state_store=state_store)
```

### Strategy Pattern

Pluggable infrastructure via Protocol adherence:

```python
# Same code, different stores
store = InMemoryEventStore()          # Dev
store = PostgreSQLEventStore(conn)    # Production
```

---

## Event Flow

```
Client
  │
  ├─► bus.publish(Command)
  │
MessageBus
  │
  ├─► CommandHandler.handle()
  │     │
  │     ├─► AggregateRepository.load()  — EventStore.load()
  │     ├─► aggregate.do_something()    — business logic
  │     ├─► AggregateRepository.save()  — EventStore.save()
  │     └─► bus.publish(Event)          — notify subscribers
  │
  └─► Event Handlers
        ├─► Projection (read model update)
        ├─► Notification (email, webhook)
        └─► Analytics / Logging
```

---

## CQRS Separation

```
Commands ──► Write Model (EventStore)
                  │ Events
                  ▼
             ProjectionEngine
                  │
                  ▼
            Read Models (dict, DB, search index)
                  │
                  ▼
             Queries ◄── Clients
```

---

## Technology Choices

| Choice | Rationale |
|--------|-----------|
| Python 3.12+ | Type hints, dataclasses, Protocols, `type` statement |
| `typing.Protocol` | Duck typing, no inheritance, easy mocking |
| `@dataclass(frozen=True)` | Immutable, hashable, auto-generated `__init__`/`__repr__`/`__eq__` |
| Polylith | Modular monorepo without microservice overhead |
| `uv` | Fast dependency management and virtual environments |
| `ruff` | Linting + formatting (replaces black, isort, flake8, pylint) |
| `ty` | Type checking |
| `pytest` | Flexible test framework with rich fixture support |

---

## Next Steps

- [Contributing](contributing.md) — Development setup and workflow
- [Testing](testing.md) — Test strategies and patterns
- [Async Design](../architecture/ASYNC_DESIGN.md) — Async API design document
