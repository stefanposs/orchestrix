# Testing

Testing strategies for Orchestrix — from unit to integration tests.

---

## Test Setup

### Install dependencies

```bash
uv sync --all-extras --dev
```

### Run tests

```bash
just test          # All tests
just test-cov      # With coverage report
just test-watch    # Re-run on file change
```

### Test Structure

```
test/
├── conftest.py                          # Shared fixtures (bus, store)
├── components/orchestrix/
│   ├── core/
│   │   ├── test_message.py              # Message creation and metadata
│   │   ├── test_aggregate_repository.py # AggregateRoot + Repository
│   │   ├── test_saga.py                 # Saga execution and compensation
│   │   ├── test_projection_engine.py    # Projection processing
│   │   ├── test_versioning.py           # Event upcasting
│   │   ├── test_validation.py           # Built-in validators
│   │   ├── test_retry.py               # Retry policies
│   │   ├── test_observability.py        # ObservabilityHooks
│   │   ├── test_logging.py             # StructuredLogger
│   │   ├── test_snapshot.py            # Snapshot save/load
│   │   ├── test_dead_letter_queue.py   # DLQ handling
│   │   ├── test_error_handling.py      # Exception paths
│   │   ├── test_edge_cases.py          # Boundary conditions
│   │   └── test_message_metadata.py    # CloudEvents fields
│   └── infrastructure/
│       ├── test_inmemory_bus.py         # InMemoryMessageBus
│       ├── test_inmemory_store.py       # InMemoryEventStore
│       ├── test_async_bus.py            # InMemoryAsyncMessageBus
│       ├── test_async_store.py          # InMemoryAsyncEventStore
│       ├── test_postgres_store.py       # PostgreSQLEventStore (testcontainers)
│       ├── test_prometheus_metrics.py   # PrometheusMetrics
│       ├── test_tracing.py             # JaegerTracer
│       └── …
├── benchmarks/                          # Performance benchmarks
└── projects/                            # Project-level integration tests
```

---

## Shared Fixtures

The root `conftest.py` provides pre-built fixtures:

```python
# test/conftest.py
from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus

@pytest.fixture
def bus():
    """Fresh InMemoryMessageBus for each test."""
    return InMemoryMessageBus()

@pytest.fixture
def store():
    """Fresh InMemoryEventStore for each test."""
    return InMemoryEventStore()
```

Use them in any test:

```python
def test_handler_stores_events(bus, store):
    handler = CreateOrderHandler(bus, store)
    bus.subscribe(CreateOrder, handler.handle)
    bus.publish(CreateOrder(order_id="ORD-001", customer_id="CUST-123"))

    events = store.load("ORD-001")
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
```

---

## Unit Tests

### Testing Messages

```python
from orchestrix.core.messaging.message import Command

def test_command_creation():
    """Test command with auto-generated metadata."""
    command = CreateOrder(order_id="ORD-001", customer_id="CUST-123")

    assert command.order_id == "ORD-001"
    assert command.type == "CreateOrder"  # Auto-derived from class name
    assert command.id  # UUID auto-generated
    assert command.specversion == "1.0"
```

### Testing Aggregates

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRoot

def test_aggregate_applies_events():
    """Test that _apply_event tracks uncommitted events."""
    account = BankAccount(aggregate_id="ACC-001")
    account.open("Alice", 1000.0)

    assert account.owner == "Alice"
    assert account.balance == 1000.0
    assert len(account.uncommitted_events) == 1
    assert isinstance(account.uncommitted_events[0], AccountOpened)

def test_aggregate_mark_committed():
    """Test that mark_events_committed clears the list."""
    account = BankAccount(aggregate_id="ACC-001")
    account.open("Alice", 1000.0)
    account.mark_events_committed()

    assert len(account.uncommitted_events) == 0
```

### Testing Validation

```python
from orchestrix.core.common.validation import validate_not_empty, ValidationError

def test_validation_rejects_empty():
    with pytest.raises(ValidationError):
        validate_not_empty("", "name")

def test_validation_accepts_value():
    validate_not_empty("Alice", "name")  # No error
```

---

## Integration Tests

### Testing with AggregateRepository

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore

def test_repository_round_trip():
    """Test save and load through repository."""
    store = InMemoryEventStore()
    repo = AggregateRepository(event_store=store)

    # Create and save
    account = BankAccount(aggregate_id="ACC-001")
    account.open("Alice", 500.0)
    repo.save(account)

    # Load and verify
    loaded = repo.load(BankAccount, "ACC-001")
    assert loaded.owner == "Alice"
    assert loaded.balance == 500.0
    assert loaded.version == 1
```

### Testing with MessageBus

```python
def test_event_handler_called(bus):
    """Test that event handlers receive published events."""
    received = []
    bus.subscribe(OrderCreated, lambda e: received.append(e))

    bus.publish(OrderCreated(order_id="ORD-001"))

    assert len(received) == 1
    assert received[0].order_id == "ORD-001"
```

### Testing Async Code

```python
import pytest
from orchestrix.infrastructure.memory.async_bus import InMemoryAsyncMessageBus

@pytest.mark.asyncio
async def test_async_bus_publish():
    """Test async message bus publishes to handlers."""
    bus = InMemoryAsyncMessageBus()
    received = []

    async def handler(event: OrderCreated) -> None:
        received.append(event)

    bus.subscribe(OrderCreated, handler)
    await bus.publish(OrderCreated(order_id="ORD-001"))

    assert len(received) == 1
```

---

## Test Patterns

### Message Spy

Collect all published messages for assertions:

```python
class MessageSpy:
    def __init__(self):
        self.messages: list[Message] = []

    def record(self, message: Message) -> None:
        self.messages.append(message)

    def get_by_type(self, message_type: type) -> list[Message]:
        return [m for m in self.messages if isinstance(m, message_type)]

@pytest.fixture
def spy(bus):
    s = MessageSpy()
    bus.subscribe(OrderCreated, s.record)
    bus.subscribe(OrderCancelled, s.record)
    return s

def test_with_spy(bus, spy):
    bus.publish(OrderCreated(order_id="ORD-001"))
    assert len(spy.get_by_type(OrderCreated)) == 1
```

### AAA Pattern

```python
def test_order_cancellation():
    # Arrange
    store = InMemoryEventStore()
    repo = AggregateRepository(event_store=store)

    # Act
    order = Order(aggregate_id="ORD-001")
    order.create("CUST-123")
    order.cancel()
    repo.save(order)

    # Assert
    loaded = repo.load(Order, "ORD-001")
    assert loaded.status == "cancelled"
```

### Parameterized Tests

```python
@pytest.mark.parametrize("value,field,should_raise", [
    ("", "name", True),
    ("Alice", "name", False),
    ("  ", "name", True),
])
def test_validate_not_empty(value, field, should_raise):
    if should_raise:
        with pytest.raises(ValidationError):
            validate_not_empty(value, field)
    else:
        validate_not_empty(value, field)
```

---

## PostgreSQL Integration Tests

PostgreSQL tests use [testcontainers](https://testcontainers.com/) for isolated containers:

```python
@pytest.mark.asyncio
async def test_postgres_save_and_load():
    """Requires Docker running."""
    store = PostgreSQLEventStore(connection_string="postgresql://...")
    await store.initialize()

    try:
        await store.save("ACC-001", [AccountOpened(...)])
        events = await store.load("ACC-001")
        assert len(events) == 1
    finally:
        await store.close()
```

Container versions are managed in `.container-versions.json` at the repo root.

---

## Coverage

```bash
# Run with coverage
just test-cov

# View HTML report
open output/htmlcov/index.html
```

Coverage output goes to `output/coverage.xml` and `output/htmlcov/`.

---

## Continuous Testing

### Watch Mode

```bash
just test-watch
```

Re-runs tests on every file change.

### CI Pipeline

GitHub Actions runs the full test suite on every push against Python 3.12 and 3.13 on Linux, macOS, and Windows.

---

## Next Steps

- [Architecture](architecture.md) — System design
- [Contributing](contributing.md) — Development workflow
- [Best Practices](../guide/best-practices.md) — Production patterns
