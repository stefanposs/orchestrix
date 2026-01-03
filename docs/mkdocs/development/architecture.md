# Architecture

Technical architecture and design decisions behind Orchestrix.

## Core Principles

### 1. Protocol-based Design

Orchestrix nutzt `typing.Protocol` statt Abstract Base Classes:

```python
from typing import Protocol

class MessageBus(Protocol):
    """Message bus interface - no inheritance required!"""
    
    def subscribe(self, message_type: type[Message], handler) -> None: ...
    def publish(self, message: Message) -> None: ...
```

**Vorteile:**

- ✅ Duck Typing - Pythonic!
- ✅ Keine Vererbung nötig
- ✅ Bessere IDE-Unterstützung
- ✅ Einfacher zu mocken in Tests

### 2. Immutable Messages

Alle Messages sind `frozen` dataclasses:

```python
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str
```

**Vorteile:**

- ✅ Thread-safe
- ✅ Hashable (can use in sets/dicts)
- ✅ Verhindert unerwartete Mutations
- ✅ CloudEvents-kompatibel

### 3. Event Sourcing First

Events sind die Single Source of Truth:

```python
# State = fold(events)
def from_events(events: list[Event]) -> Order:
    order = None
    for event in events:
        order = apply(order, event)
    return order
```

**Vorteile:**

- ✅ Vollständige Audit Trail
- ✅ Time Travel (State zu jedem Zeitpunkt)
- ✅ Event Replay für Projections
- ✅ Debugging & Fehleranalyse

## Architecture Layers

```
┌─────────────────────────────────────────────┐
│           Application Layer                 │
│  (Modules, Command Handlers, Use Cases)     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Domain Layer                      │
│  (Aggregates, Commands, Events)             │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Infrastructure Layer                │
│  (MessageBus, EventStore Implementations)   │
└─────────────────────────────────────────────┘
```

### Application Layer

**Responsibility:** Orchestration & Use Cases

```python
class OrderModule(Module):
    """Application-level orchestration."""
    
    def register(self, bus: MessageBus, store: EventStore) -> None:
        # Wire domain to infrastructure
        bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
        bus.subscribe(OrderCreated, self._send_email)
```

### Domain Layer

**Responsibility:** Business Logic & Rules

```python
@dataclass
class Order:
    """Domain aggregate."""
    
    def cancel(self) -> None:
        """Business rule: Can only cancel pending orders."""
        if self.status != "pending":
            raise ValueError("Can only cancel pending orders")
        self.status = "cancelled"
        self._events.append(OrderCancelled(order_id=self.order_id))
```

### Infrastructure Layer

**Responsibility:** Technical Implementation

```python
class InMemoryMessageBus(MessageBus):
    """Technical implementation of message routing."""
    
    def publish(self, message: Message) -> None:
        for handler in self._handlers[type(message)]:
            handler(message)
```

## Design Patterns

### Command Pattern

Commands encapsulate requests:

```python
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    """Command = Request to do something."""
    order_id: str
    customer_id: str

# Execute via handler
handler.handle(CreateOrder(...))
```

### Observer Pattern

MessageBus implements observer:

```python
# Subscribe observers
bus.subscribe(OrderCreated, send_email)
bus.subscribe(OrderCreated, update_inventory)
bus.subscribe(OrderCreated, log_event)

# Notify all observers
bus.publish(OrderCreated(...))
```

### Repository Pattern

EventStore is a repository:

```python
# Save aggregate state (as events)
store.save(aggregate_id, events)

# Load aggregate state (from events)
events = store.load(aggregate_id)
aggregate = reconstruct(events)
```

### Strategy Pattern

Pluggable infrastructure:

```python
# Strategy 1: In-Memory
bus = InMemoryMessageBus()

# Strategy 2: Redis (future)
bus = RedisMessageBus(url)

# Strategy 3: RabbitMQ (future)
bus = RabbitMQMessageBus(url)

# Same interface, different implementation!
```

## Event Flow

```
1. Client
   │
   ├─► publish(Command)
   │
2. MessageBus
   │
   ├─► route to CommandHandler
   │
3. CommandHandler
   │
   ├─► load Events from EventStore
   ├─► reconstruct Aggregate
   ├─► execute business logic
   ├─► collect new Events
   ├─► save Events to EventStore
   │
   └─► publish Events to MessageBus
       │
4. MessageBus
   │
   └─► notify all Event Handlers
       │
       ├─► Projection Handler
       ├─► Email Handler
       ├─► Analytics Handler
       └─► ...
```

## Scalability Considerations

### Current (v0.1.0)

- ✅ Single process
- ✅ Synchronous
- ✅ In-memory storage
- ✅ Perfect for: Monoliths, testing, development

### Future Scaling

#### Horizontal Scaling

```python
# Distributed message bus
bus = RedisMessageBus("redis://...")

# Multiple instances can publish/subscribe
# Events are distributed across workers
```

#### Async Processing

```python
class AsyncMessageBus(MessageBus):
    async def publish(self, message: Message) -> None:
        """Non-blocking event publishing."""
        tasks = [handler(message) for handler in handlers]
        await asyncio.gather(*tasks)
```

#### Event Streaming

```python
# Kafka for high-throughput events
bus = KafkaMessageBus("kafka://...")

# Process millions of events/sec
```

#### CQRS Separation

```
Commands ──► Write Model (Event Store)
                  │
                  │ Events
                  │
                  ▼
             Event Handlers
                  │
                  ▼
            Read Models (PostgreSQL, Elasticsearch, ...)
                  │
                  ▼
             Queries ◄── Clients
```

## Technology Choices

### Why Python?

- ✅ Type hints für Type Safety
- ✅ Dataclasses für Value Objects
- ✅ Protocols für Interfaces
- ✅ Rich ecosystem
- ✅ Widely adopted

### Why Protocols over ABC?

```python
# ❌ Abstract Base Class - requires inheritance
class MessageBus(ABC):
    @abstractmethod
    def publish(self, message: Message) -> None:
        pass

class MyBus(MessageBus):  # Must inherit!
    def publish(self, message: Message) -> None:
        pass

# ✅ Protocol - duck typing
class MessageBus(Protocol):
    def publish(self, message: Message) -> None: ...

class MyBus:  # No inheritance needed!
    def publish(self, message: Message) -> None:
        pass
```

### Why Dataclasses?

```python
# ✅ Immutable, type-safe, clean
@dataclass(frozen=True, kw_only=True)
class Order(Command):
    order_id: str
    customer_id: str

# Automatically generates:
# - __init__
# - __repr__
# - __eq__
# - __hash__ (because frozen)
```

### Why Event Sourcing?

```python
# Traditional: Current state only
order = db.query(Order).get(order_id)
# Lost: How did we get here? Who made changes? When?

# Event Sourcing: Complete history
events = store.load(order_id)
# Have: Every change, every reason, complete audit trail
```

## Performance Characteristics

### InMemoryMessageBus

- **Subscribe:** O(1)
- **Publish:** O(n) where n = handlers for message type
- **Memory:** O(m) where m = total subscriptions

### InMemoryEventStore

- **Save:** O(1) append
- **Load:** O(n) where n = events for aggregate
- **Memory:** O(e) where e = total events

### Optimization: Snapshots

For aggregates with many events (> 1000):

```python
# Without snapshot: Load 10,000 events
events = store.load(aggregate_id)  # Slow!
order = Order.from_events(events)

# With snapshot: Load snapshot + recent events
snapshot = snapshot_store.load(aggregate_id)
recent_events = store.load_after_version(aggregate_id, snapshot.version)
order = snapshot.aggregate
for event in recent_events:
    order.apply(event)
```

## Extensibility Points

Orchestrix is designed to be extended:

### 1. Custom Message Types

```python
@dataclass(frozen=True, kw_only=True)
class Query(Message):
    """New message type for queries."""
    pass

class GetOrder(Query):
    order_id: str
```

### 2. Custom Bus Implementations

```python
class RateLimitedBus(MessageBus):
    """Bus with rate limiting."""
    
    def publish(self, message: Message) -> None:
        if self._rate_limiter.allow():
            self._inner_bus.publish(message)
        else:
            raise RateLimitExceeded()
```

### 3. Custom Store Implementations

```python
class PostgreSQLEventStore(EventStore):
    """Production-grade PostgreSQL store."""
    
    def save(self, aggregate_id: str, events: list[Event]) -> None:
        # Implement with psycopg2/asyncpg
        pass
```

### 4. Middleware/Decorators

```python
def logged(handler):
    """Decorator for logging handlers."""
    def wrapper(message):
        logger.info(f"Handling {type(message).__name__}")
        result = handler(message)
        logger.info(f"Handled {type(message).__name__}")
        return result
    return wrapper

@logged
def handle_create_order(command: CreateOrder):
    # Implementation
    pass
```

## Testing Architecture

Testable by design:

```python
# Production
bus = RedisMessageBus("redis://prod")
store = PostgreSQLEventStore("postgresql://prod")

# Testing
bus = InMemoryMessageBus()
store = InMemoryEventStore()

# Same interface - tests pass!
```

## Future Roadmap

### v0.2.0 - Async Support

- AsyncMessageBus
- AsyncEventStore
- Async handlers

### v0.3.0 - Persistence

- PostgreSQL EventStore
- MongoDB EventStore
- SQLite EventStore

### v0.4.0 - Distributed

- Redis MessageBus
- RabbitMQ MessageBus
- Kafka Integration

### v1.0.0 - Production Ready

- Saga Support
- Process Managers
- Outbox Pattern
- Event Versioning

## Architecture Decisions

See ADR (Architecture Decision Records) in `/docs/adr/`:

- ADR-001: Use Protocols over ABC
- ADR-002: Immutable Messages with Dataclasses
- ADR-003: Event Sourcing by Default
- ADR-004: CloudEvents Compatibility

## Next Steps

- [Contributing](contributing.md) - How to contribute
- [Testing](testing.md) - Test strategies
- [Best Practices](../guide/best-practices.md) - Production guidelines
