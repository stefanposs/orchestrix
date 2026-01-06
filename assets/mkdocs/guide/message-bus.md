# Message Bus

Der Message Bus ist das Herzstück der Event-Driven Architecture - er routet alle Messages zu ihren Handlers.

## Was ist ein Message Bus?

Ein **Message Bus**:

- Nimmt Messages entgegen (Commands & Events)
- Routet sie zu registrierten Handlers
- Entkoppelt Publisher von Subscribern
- Ermöglicht 1-zu-N Kommunikation

## Basic Usage

```python
from orchestrix import InMemoryMessageBus, Command, Event

# Create bus
bus = InMemoryMessageBus()

# Subscribe handlers
bus.subscribe(CreateOrder, create_order_handler)
bus.subscribe(OrderCreated, send_email_handler)
bus.subscribe(OrderCreated, update_inventory_handler)

# Publish messages
bus.publish(CreateOrder(order_id="ORD-001", ...))
```

## InMemoryMessageBus

Der `InMemoryMessageBus` ist die Standard-Implementierung - perfekt für:

- ✅ Entwicklung & Testing
- ✅ Einfache Applikationen
- ✅ Monolithen
- ✅ Schnelle Prototypen

```python
from orchestrix import InMemoryMessageBus

bus = InMemoryMessageBus()

# Subscribe: Message Type → Handler
bus.subscribe(CreateOrder, create_order_handler)

# Publish: Alle Handler werden synchron aufgerufen
bus.publish(CreateOrder(order_id="ORD-001", ...))
```

### Wie es funktioniert

```python
from collections import defaultdict
from orchestrix import Message, MessageBus

class InMemoryMessageBus(MessageBus):
    def __init__(self) -> None:
        self._handlers: dict[type[Message], list] = defaultdict(list)
    
    def subscribe(self, message_type: type[Message], handler) -> None:
        """Register a handler for a message type."""
        self._handlers[message_type].append(handler)
    
    def publish(self, message: Message) -> None:
        """Publish to all registered handlers."""
        for handler in self._handlers[type(message)]:
            if callable(handler):
                handler(message)
            elif hasattr(handler, "handle"):
                handler.handle(message)
```

## Handler Types

### 1. Function Handler

```python
def handle_order_created(event: OrderCreated) -> None:
    print(f"Order {event.order_id} created!")

bus.subscribe(OrderCreated, handle_order_created)
```

### 2. Lambda Handler

```python
bus.subscribe(
    OrderCreated,
    lambda e: print(f"Order {e.order_id} created!")
)
```

### 3. Class-based Handler

```python
from orchestrix import CommandHandler

class CreateOrderHandler(CommandHandler[CreateOrder]):
    def __init__(self, bus: MessageBus, store: EventStore):
        self.bus = bus
        self.store = store
    
    def handle(self, command: CreateOrder) -> None:
        # Business logic here
        order = Order.create(command.order_id, ...)
        events = order.collect_events()
        self.store.save(command.order_id, events)
        for event in events:
            self.bus.publish(event)

bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
```

### 4. Method Handler

```python
class OrderService:
    def __init__(self, db):
        self.db = db
    
    def on_order_created(self, event: OrderCreated) -> None:
        self.db.save_order(event)

service = OrderService(db)
bus.subscribe(OrderCreated, service.on_order_created)
```

## Subscription Patterns

### One Handler per Command

Commands sollten **genau einen Handler** haben:

```python
# ✅ Gut: 1 Command → 1 Handler
bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
bus.subscribe(CancelOrder, CancelOrderHandler(bus, store))

# ❌ Vermeiden: Multiple Handler für Commands
bus.subscribe(CreateOrder, handler1)
bus.subscribe(CreateOrder, handler2)  # Wer ist verantwortlich?
```

### Multiple Handlers per Event

Events können **mehrere Handler** haben:

```python
# ✅ Gut: 1 Event → N Handler
bus.subscribe(OrderCreated, send_confirmation_email)
bus.subscribe(OrderCreated, update_inventory)
bus.subscribe(OrderCreated, send_to_analytics)
bus.subscribe(OrderCreated, notify_warehouse)
```

## Error Handling

### Current Behavior

Der `InMemoryMessageBus` hat **keine eingebaute Error Handling**:

```python
def failing_handler(event: OrderCreated) -> None:
    raise ValueError("Something went wrong!")

bus.subscribe(OrderCreated, failing_handler)
bus.subscribe(OrderCreated, working_handler)  # Wird nicht aufgerufen!

bus.publish(OrderCreated(...))  # Raises ValueError
```

### Robust Handler Pattern

Wrap deine Handler für besseres Error Handling:

```python
def safe_handler(handler):
    """Decorator für safe handlers."""
    def wrapper(message):
        try:
            return handler(message)
        except Exception as e:
            print(f"❌ Error in handler: {e}")
            # Log to monitoring system
            # Send to dead letter queue
    return wrapper

@safe_handler
def send_email(event: OrderCreated) -> None:
    # Can fail without breaking other handlers
    email_service.send(...)

bus.subscribe(OrderCreated, send_email)
```

## Testing with Message Bus

```python
import pytest
from orchestrix import InMemoryMessageBus

def test_order_creation():
    # Arrange
    bus = InMemoryMessageBus()
    events_received = []
    
    bus.subscribe(OrderCreated, lambda e: events_received.append(e))
    
    # Act
    bus.publish(OrderCreated(order_id="ORD-001", ...))
    
    # Assert
    assert len(events_received) == 1
    assert events_received[0].order_id == "ORD-001"
```

### Test Spy Pattern

```python
class MessageSpy:
    """Collect all published messages for testing."""
    
    def __init__(self):
        self.messages = []
    
    def record(self, message):
        self.messages.append(message)
    
    def get_by_type(self, message_type):
        return [m for m in self.messages if isinstance(m, message_type)]

# Usage in tests
spy = MessageSpy()
bus.subscribe(OrderCreated, spy.record)
bus.subscribe(OrderShipped, spy.record)

# ... run test code ...

created_events = spy.get_by_type(OrderCreated)
assert len(created_events) == 1
```

## Advanced: Custom Bus Implementation

Du kannst eigene Bus-Implementierungen erstellen:

```python
from orchestrix import MessageBus, Message

class AsyncMessageBus(MessageBus):
    """Async message bus using asyncio."""
    
    def __init__(self):
        self._handlers = defaultdict(list)
    
    def subscribe(self, message_type: type[Message], handler) -> None:
        self._handlers[message_type].append(handler)
    
    async def publish_async(self, message: Message) -> None:
        """Publish message asynchronously."""
        tasks = []
        for handler in self._handlers[type(message)]:
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(message))
            else:
                tasks.append(asyncio.to_thread(handler, message))
        
        await asyncio.gather(*tasks, return_exceptions=True)
```

## Future: Alternative Buses

Orchestrix ist designed für pluggable Buses:

### Redis Message Bus

```python
class RedisMessageBus(MessageBus):
    """Distributed message bus using Redis Pub/Sub."""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self._handlers = defaultdict(list)
    
    def subscribe(self, message_type, handler):
        channel = message_type.__name__
        self._handlers[channel].append(handler)
        # Subscribe to Redis channel
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
    
    def publish(self, message: Message):
        channel = type(message).__name__
        # Serialize and publish to Redis
        self.redis.publish(channel, serialize(message))
```

### RabbitMQ Message Bus

```python
class RabbitMQMessageBus(MessageBus):
    """Enterprise message bus using RabbitMQ."""
    
    def __init__(self, connection_string: str):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(connection_string)
        )
        self.channel = self.connection.channel()
```

## Best Practices

### ✅ DO

- **Synchrone Handler** für kritische Business Logic
- **Idempotente Handler** - können mehrfach aufgerufen werden
- **Kleine Handler** - Single Responsibility
- **Error Handling** - Wrapper für robuste Handler

### ❌ DON'T

- **Lange laufende Tasks** im Handler - use async/queue
- **Handler mit Side Effects** ohne Error Handling
- **Multiple Command Handlers** - unclear responsibility
- **Handler die auf Handler warten** - Deadlock Risk

## Next Steps

- [Event Store](event-store.md) - Persistence Patterns
- [Best Practices](best-practices.md) - Production Guidelines
- [Testing](../development/testing.md) - Test Strategies
