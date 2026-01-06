# Best Practices

Production-ready Patterns für Orchestrix - kein Bullshit! 🚀

## Domain Design

### Bounded Contexts

Jedes Module = ein Bounded Context:

```python
# ✅ Gut: Klare Grenzen
class OrderModule(Module): pass      # Order Domain
class PaymentModule(Module): pass    # Payment Domain
class ShippingModule(Module): pass   # Shipping Domain

# ❌ Schlecht: God Module
class EverythingModule(Module): pass  # Too broad!
```

### Aggregate Boundaries

```python
# ✅ Gut: Kleine, fokussierte Aggregates
class Order:
    order_id: str
    customer_id: str  # Referenz!
    items: list[OrderItem]

# ❌ Schlecht: Zu groß
class Order:
    order_id: str
    customer: Customer        # Nested aggregate!
    items: list[Product]      # Nested aggregates!
    shipping: ShippingInfo    # Could be separate!
```

### Event Granularity

```python
# ✅ Gut: Spezifische Events
OrderPlaced(order_id, items, total)
OrderPaid(order_id, payment_id, amount)
OrderShipped(order_id, tracking_number)
OrderCancelled(order_id, reason)

# ❌ Schlecht: Generische Events
OrderUpdated(order_id, field, value)  # Was wurde geändert?
OrderChanged(order_id, data)          # Zu vage!
```

## Error Handling

### Command Validation

```python
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    items: list[dict]
    
    def __post_init__(self) -> None:
        """Validate before processing."""
        if not self.items:
            raise ValueError("Order must have at least one item")
        if any(item["quantity"] <= 0 for item in self.items):
            raise ValueError("Quantity must be positive")
```

### Handler Error Handling

```python
class CreateOrderHandler(CommandHandler[CreateOrder]):
    def handle(self, command: CreateOrder) -> None:
        try:
            order = Order.create(command.order_id, command.items)
            events = order.collect_events()
            self.store.save(command.order_id, events)
            for event in events:
                self.bus.publish(event)
        
        except ValueError as e:
            # Business rule violation
            logger.warning(f"Order creation failed: {e}")
            self.bus.publish(OrderCreationFailed(
                order_id=command.order_id,
                reason=str(e)
            ))
        
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise  # Re-raise for retry logic
```

### Safe Event Handlers

```python
def safe_event_handler(handler):
    """Decorator for safe event handlers."""
    def wrapper(event):
        try:
            return handler(event)
        except Exception as e:
            logger.error(
                f"Event handler failed: {handler.__name__}",
                exc_info=True,
                extra={"event": event}
            )
            # Don't re-raise - other handlers should still run
    return wrapper

@safe_event_handler
def send_email(event: OrderCreated) -> None:
    email_service.send(...)
```

## Testing

### Unit Tests

```python
def test_order_creation():
    # Test aggregate logic in isolation
    order = Order.create("ORD-001", [{"sku": "A", "qty": 2}])
    
    events = order.collect_events()
    
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
    assert events[0].order_id == "ORD-001"
```

### Integration Tests

```python
def test_order_module_integration():
    # Test with real infrastructure
    bus = InMemoryMessageBus()
    store = InMemoryEventStore()
    
    module = OrderModule()
    module.register(bus, store)
    
    # Execute command
    bus.publish(CreateOrder(order_id="ORD-001", ...))
    
    # Verify events stored
    events = store.load("ORD-001")
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
```

### Test Fixtures

```python
@pytest.fixture
def bus():
    return InMemoryMessageBus()

@pytest.fixture
def store():
    return InMemoryEventStore()

@pytest.fixture
def order_module(bus, store):
    module = OrderModule()
    module.register(bus, store)
    return module

def test_with_fixtures(order_module, bus):
    bus.publish(CreateOrder(...))
    # Test logic
```

## Performance

### Event Store Optimization

```python
# ❌ Schlecht: Load all events every time
events = store.load(aggregate_id)  # Could be 10,000 events!
order = Order.from_events(events)

# ✅ Besser: Snapshots for large aggregates
snapshot = snapshot_store.load(aggregate_id)
events_after_snapshot = store.load_after_version(
    aggregate_id,
    snapshot.version
)
order = snapshot.aggregate
for event in events_after_snapshot:
    order.apply(event)
```

### Snapshot Pattern

```python
@dataclass
class Snapshot:
    aggregate_id: str
    version: int
    state: dict
    created_at: str

class SnapshotStore:
    def save_snapshot(self, aggregate_id: str, version: int, state: dict):
        """Save aggregate snapshot every N events."""
        if version % 100 == 0:  # Every 100 events
            self.snapshots[aggregate_id] = Snapshot(
                aggregate_id=aggregate_id,
                version=version,
                state=state,
                created_at=datetime.utcnow().isoformat()
            )
```

### Batch Processing

```python
# ✅ Batch event publishing
events = []
for order in orders:
    events.extend(order.collect_events())

# Save all at once
for aggregate_id in set(e.aggregate_id for e in events):
    aggregate_events = [e for e in events if e.aggregate_id == aggregate_id]
    store.save(aggregate_id, aggregate_events)

# Publish all
for event in events:
    bus.publish(event)
```

## Production Readiness

### Logging

```python
import logging

logger = logging.getLogger(__name__)

class CreateOrderHandler(CommandHandler[CreateOrder]):
    def handle(self, command: CreateOrder) -> None:
        logger.info(
            "Processing CreateOrder",
            extra={
                "command_id": command.id,
                "order_id": command.order_id,
                "customer_id": command.customer_id
            }
        )
        
        try:
            # Business logic
            logger.info(f"Order {command.order_id} created successfully")
        except Exception as e:
            logger.error(
                f"Failed to create order {command.order_id}",
                exc_info=True
            )
            raise
```

### Monitoring

```python
from prometheus_client import Counter, Histogram

commands_processed = Counter(
    'commands_processed_total',
    'Total commands processed',
    ['command_type', 'status']
)

command_duration = Histogram(
    'command_duration_seconds',
    'Command processing duration',
    ['command_type']
)

class MonitoredHandler(CommandHandler[CreateOrder]):
    @command_duration.labels(command_type='CreateOrder').time()
    def handle(self, command: CreateOrder) -> None:
        try:
            # Process command
            commands_processed.labels(
                command_type='CreateOrder',
                status='success'
            ).inc()
        except Exception:
            commands_processed.labels(
                command_type='CreateOrder',
                status='error'
            ).inc()
            raise
```

### Configuration

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    database_url: str
    redis_url: str
    log_level: str = "INFO"
    enable_snapshots: bool = True
    snapshot_interval: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()

# Use in application
if settings.enable_snapshots:
    snapshot_store = SnapshotStore(settings.database_url)
```

## Security

### Sensitive Data

```python
# ❌ Nie sensitive Daten in Events
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str
    password_hash: str  # ❌ Nicht in Event Stream!
    credit_card: str    # ❌ NIEMALS!

# ✅ Nur IDs und non-sensitive Daten
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str
    # Sensitive data in separate store
```

### Audit Trail

```python
@dataclass(frozen=True, kw_only=True)
class Command(Message):
    user_id: str = ""  # Who executed?
    trace_id: str = ""  # Request tracking
    
@dataclass(frozen=True, kw_only=True)
class Event(Message):
    correlation_id: str = ""  # Which command?
    causation_id: str = ""    # Which event?
```

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Health Checks

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        store.load("test")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 503
```

## Common Pitfalls

### ❌ Event Store als Query DB

```python
# ❌ Schlecht: Query event store
events = store.load_all()
orders = [e for e in events if isinstance(e, OrderCreated)]
# Langsam und ineffizient!

# ✅ Gut: Separate Read Model
class OrderReadModel:
    def __init__(self):
        self.orders = {}
    
    def on_order_created(self, event: OrderCreated):
        self.orders[event.order_id] = {
            "id": event.order_id,
            "customer": event.customer_id,
            "status": "pending"
        }
    
    def find_by_customer(self, customer_id: str):
        return [o for o in self.orders.values() 
                if o["customer"] == customer_id]
```

### ❌ Commands zwischen Modules

```python
# ❌ Schlecht
class InventoryModule(Module):
    def on_order_created(self, event: OrderCreated):
        # DON'T: Send command to other module!
        self.bus.publish(ReserveInventory(...))

# ✅ Gut: Events only
class InventoryModule(Module):
    def on_order_created(self, event: OrderCreated):
        # Emit own event
        self.bus.publish(InventoryReserved(...))
```

### ❌ Mutable Aggregates

```python
# ❌ Schlecht
def handle_cancel_order(command: CancelOrder):
    order = get_order(command.order_id)  # From cache
    order.cancel()  # Mutates shared state!

# ✅ Gut
def handle_cancel_order(command: CancelOrder):
    events = store.load(command.order_id)
    order = Order.from_events(events)  # Fresh instance
    order.cancel()
```

## Next Steps

- [Testing](../development/testing.md) - Comprehensive Test Strategies
- [Architecture](../development/architecture.md) - System Design
- [Contributing](../development/contributing.md) - Contribute to Orchestrix
