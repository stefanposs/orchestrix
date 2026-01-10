# Testing

Comprehensive testing strategies for Orchestrix - from unit to integration tests.

## Test Setup

### Installation

```bash
# Install with test dependencies
uv sync --all-extras --dev

# Or with pip
pip install orchestrix[test]
```

### Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_message.py        # Message tests
│   ├── test_aggregate.py      # Aggregate tests
│   └── test_handlers.py       # Handler tests
├── integration/
│   ├── test_order_module.py   # Module integration tests
│   └── test_event_flow.py     # End-to-end flows
└── performance/
    └── test_event_store.py    # Performance tests
```

## Unit Tests

### Testing Messages

```python
def test_command_creation():
    """Test command with valid data."""
    command = CreateOrder(
        order_id="ORD-001",
        customer_id="CUST-123",
        items=[{"sku": "A", "qty": 2}]
    )
    
    assert command.order_id == "ORD-001"
    assert command.customer_id == "CUST-123"
    assert len(command.items) == 1
    assert command.type == "CreateOrder"
    assert command.id  # Auto-generated UUID

def test_command_validation():
    """Test command validation in __post_init__."""
    with pytest.raises(ValueError, match="Order must have items"):
        CreateOrder(
            order_id="ORD-001",
            customer_id="CUST-123",
            items=[]  # Invalid!
        )
```

### Testing Aggregates

```python
def test_order_creation():
    """Test aggregate creation."""
    order = Order.create(
        order_id="ORD-001",
        customer_id="CUST-123",
        items=[{"sku": "A", "qty": 2}]
    )
    
    assert order.order_id == "ORD-001"
    assert order.status == "pending"
    
    # Check events
    events = order.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)

def test_order_cancellation():
    """Test aggregate business logic."""
    order = Order.create("ORD-001", "CUST-123", [])
    order.cancel()
    
    assert order.status == "cancelled"
    
    events = order.collect_events()
    assert any(isinstance(e, OrderCancelled) for e in events)

def test_order_cannot_cancel_if_shipped():
    """Test business rule enforcement."""
    order = Order.create("ORD-001", "CUST-123", [])
    order.status = "shipped"  # Simulate shipping
    
    with pytest.raises(ValueError, match="Cannot cancel shipped order"):
        order.cancel()
```

### Testing Event Reconstruction

```python
def test_aggregate_reconstruction():
    """Test rebuilding aggregate from events."""
    events = [
        OrderCreated(order_id="ORD-001", customer_id="CUST-123"),
        ItemAdded(order_id="ORD-001", item={"sku": "A"}),
        ItemAdded(order_id="ORD-001", item={"sku": "B"}),
        OrderPaid(order_id="ORD-001", payment_id="PAY-001")
    ]
    
    order = Order.from_events(events)
    
    assert order.order_id == "ORD-001"
    assert len(order.items) == 2
    assert order.status == "paid"
```

## Integration Tests

### Testing with MessageBus

```python
@pytest.fixture
def bus():
    """Provide clean message bus."""
    return InMemoryMessageBus()

@pytest.fixture
def store():
    """Provide clean event store."""
    return InMemoryEventStore()

def test_command_handler_integration(bus, store):
    """Test command handler with infrastructure."""
    # Register handler
    handler = CreateOrderHandler(bus, store)
    bus.subscribe(CreateOrder, handler)
    
    # Execute command
    command = CreateOrder(
        order_id="ORD-001",
        customer_id="CUST-123",
        items=[{"sku": "A", "qty": 2}]
    )
    bus.publish(command)
    
    # Verify events stored
    events = store.load("ORD-001")
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
```

### Testing Event Handlers

```python
def test_event_handler_called(bus):
    """Test that event handlers are invoked."""
    events_received = []
    
    # Subscribe event handler
    bus.subscribe(OrderCreated, lambda e: events_received.append(e))
    
    # Publish event
    event = OrderCreated(order_id="ORD-001", customer_id="CUST-123")
    bus.publish(event)
    
    # Verify handler was called
    assert len(events_received) == 1
    assert events_received[0].order_id == "ORD-001"

def test_multiple_event_handlers(bus):
    """Test multiple handlers for same event."""
    handler1_called = []
    handler2_called = []
    
    bus.subscribe(OrderCreated, lambda e: handler1_called.append(e))
    bus.subscribe(OrderCreated, lambda e: handler2_called.append(e))
    
    event = OrderCreated(order_id="ORD-001", customer_id="CUST-123")
    bus.publish(event)
    
    assert len(handler1_called) == 1
    assert len(handler2_called) == 1
```

### Testing Complete Modules

```python
def test_order_module(bus, store):
    """Test complete module registration and execution."""
    # Register module
    module = OrderModule()
    module.register(bus, store)
    
    # Execute command
    bus.publish(CreateOrder(
        order_id="ORD-001",
        customer_id="CUST-123",
        items=[{"sku": "A", "qty": 2}]
    ))
    
    # Verify events
    events = store.load("ORD-001")
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
    
    # Execute another command
    bus.publish(CancelOrder(order_id="ORD-001"))
    
    # Verify new events
    events = store.load("ORD-001")
    assert len(events) == 2
    assert isinstance(events[1], OrderCancelled)
```

## Test Patterns

### Message Spy Pattern

Collect all messages for assertions:

```python
class MessageSpy:
    """Spy to collect published messages."""
    
    def __init__(self):
        self.messages = []
    
    def record(self, message):
        self.messages.append(message)
    
    def get_by_type(self, message_type):
        return [m for m in self.messages if isinstance(m, message_type)]
    
    def count(self, message_type):
        return len(self.get_by_type(message_type))

@pytest.fixture
def message_spy(bus):
    """Provide message spy."""
    spy = MessageSpy()
    # Subscribe to all message types
    bus.subscribe(OrderCreated, spy.record)
    bus.subscribe(OrderCancelled, spy.record)
    return spy

def test_with_spy(bus, message_spy):
    """Test using message spy."""
    bus.publish(OrderCreated(order_id="ORD-001", ...))
    
    assert message_spy.count(OrderCreated) == 1
    assert message_spy.count(OrderCancelled) == 0
```

### Fake/Mock Pattern

```python
class FakeEventStore(EventStore):
    """Fake event store for testing."""
    
    def __init__(self):
        self.saved_events = {}
        self.load_calls = []
    
    def save(self, aggregate_id: str, events: list[Event]) -> None:
        if aggregate_id not in self.saved_events:
            self.saved_events[aggregate_id] = []
        self.saved_events[aggregate_id].extend(events)
    
    def load(self, aggregate_id: str) -> list[Event]:
        self.load_calls.append(aggregate_id)
        return self.saved_events.get(aggregate_id, [])

def test_with_fake_store():
    """Test using fake store."""
    store = FakeEventStore()
    
    # Use fake in test
    handler = CreateOrderHandler(bus, store)
    handler.handle(CreateOrder(...))
    
    # Assert on fake
    assert "ORD-001" in store.saved_events
    assert len(store.load_calls) == 0
```

### Parameterized Tests

```python
@pytest.mark.parametrize("status,can_cancel", [
    ("pending", True),
    ("paid", True),
    ("shipped", False),
    ("cancelled", False),
])
def test_order_cancellation_rules(status, can_cancel):
    """Test cancellation rules for different statuses."""
    order = Order.create("ORD-001", "CUST-123", [])
    order.status = status
    
    if can_cancel:
        order.cancel()
        assert order.status == "cancelled"
    else:
        with pytest.raises(ValueError):
            order.cancel()
```

## Testing Best Practices

### AAA Pattern

Arrange-Act-Assert:

```python
def test_order_creation():
    # Arrange
    bus = InMemoryMessageBus()
    store = InMemoryEventStore()
    handler = CreateOrderHandler(bus, store)
    bus.subscribe(CreateOrder, handler)
    
    # Act
    bus.publish(CreateOrder(order_id="ORD-001", ...))
    
    # Assert
    events = store.load("ORD-001")
    assert len(events) == 1
```

### Test Isolation

```python
@pytest.fixture
def clean_bus():
    """Each test gets fresh bus."""
    return InMemoryMessageBus()

def test_1(clean_bus):
    # Test 1 doesn't affect test 2
    pass

def test_2(clean_bus):
    # Fresh bus, no state from test 1
    pass
```

### Descriptive Names

```python
# ✅ Gut
def test_order_cannot_be_cancelled_after_shipping():
    pass

def test_aggregate_emits_correct_events_on_creation():
    pass

# ❌ Schlecht
def test_order_1():
    pass

def test_stuff():
    pass
```

## Coverage

### Run with Coverage

```bash
just test-cov
```

### View HTML Report

```bash
just test-cov
open htmlcov/index.html
```

### Coverage Requirements

Orchestrix requires **100% code coverage**:

```toml
[tool.pytest.ini_options]
addopts = "--cov=orchestrix --cov-report=term --cov-report=html --cov-report=xml --cov-fail-under=100"
```

### Exclude from Coverage

Nur in Ausnahmefällen:

```python
def __repr__(self):  # pragma: no cover
    return f"Order({self.order_id})"
```

## Performance Tests

```python
import time

def test_event_store_performance():
    """Test event store can handle large event streams."""
    store = InMemoryEventStore()
    
    # Create 10,000 events
    events = [
        OrderCreated(order_id=f"ORD-{i}", ...)
        for i in range(10_000)
    ]
    
    # Measure save time
    start = time.time()
    store.save("ORD-001", events)
    duration = time.time() - start
    
    assert duration < 1.0  # Should be fast
    
    # Measure load time
    start = time.time()
    loaded = store.load("ORD-001")
    duration = time.time() - start
    
    assert len(loaded) == 10_000
    assert duration < 0.1  # Should be very fast
```

## Continuous Testing

### Watch Mode

```bash
just test-watch
```

Tests laufen bei jeder Änderung automatisch!

### Pre-commit Hooks

```bash
# Install hooks
uv run pre-commit install

# Runs automatically on git commit
git commit -m "feat: add new feature"
```

## Next Steps

- [Architecture](architecture.md) - System Design
- [Contributing](contributing.md) - Contribution Guidelines
- [Best Practices](../guide/best-practices.md) - Production Tips
