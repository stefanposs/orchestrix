# Infrastructure API Reference

## InMemoryMessageBus

In-memory implementation of the MessageBus protocol.

```python
from orchestrix import InMemoryMessageBus

bus = InMemoryMessageBus()
```

### Class Definition

```python
class InMemoryMessageBus:
    """Synchronous in-memory message bus.
    
    Suitable for:
    - Development and testing
    - Single-process applications
    - Monolithic architectures
    
    Characteristics:
    - Synchronous handler execution
    - Handlers called in subscription order
    - No persistence between restarts
    """
    
    def __init__(self) -> None:
        """Initialize empty message bus."""
```

### Methods

#### `subscribe(message_type, handler)`

Register a handler for a message type.

**Parameters:**

- `message_type` (type[Message]): The message class to handle
- `handler` (Callable | CommandHandler): Function or handler with `handle()` method

**Returns:** None

**Example:**

```python
# Function handler
def handle_order(event: OrderCreated) -> None:
    print(f"Order created: {event.order_id}")

bus.subscribe(OrderCreated, handle_order)

# Class-based handler
class CreateOrderHandler(CommandHandler[CreateOrder]):
    def handle(self, command: CreateOrder) -> None:
        # Implementation
        pass

bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))

# Lambda handler
bus.subscribe(OrderCreated, lambda e: print(f"Order: {e.order_id}"))

# Method handler
class OrderService:
    def on_order_created(self, event: OrderCreated) -> None:
        self.process(event)

service = OrderService()
bus.subscribe(OrderCreated, service.on_order_created)
```

#### `publish(message)`

Publish a message to all registered handlers.

**Parameters:**

- `message` (Message): The message to publish

**Returns:** None

**Raises:**

- Any exception from handlers (no built-in error handling)

**Example:**

```python
# Publish command
bus.publish(CreateOrder(
    order_id="ORD-001",
    customer_id="CUST-123"
))

# Publish event
bus.publish(OrderCreated(
    order_id="ORD-001",
    customer_id="CUST-123"
))
```

### Behavior

**Handler Execution:**

- Handlers are called **synchronously** in order of subscription
- If a handler raises an exception, subsequent handlers are **not** called
- No transaction management or error recovery

```python
bus.subscribe(OrderCreated, handler1)  # Called first
bus.subscribe(OrderCreated, handler2)  # Called second
bus.subscribe(OrderCreated, handler3)  # Called third

bus.publish(OrderCreated(...))  # Calls in order: 1, 2, 3
```

**Error Handling:**

```python
def failing_handler(event):
    raise ValueError("Oops!")

def working_handler(event):
    print("This won't be called!")

bus.subscribe(OrderCreated, failing_handler)
bus.subscribe(OrderCreated, working_handler)  # Never reached!

bus.publish(OrderCreated(...))  # Raises ValueError
```

### Thread Safety

⚠️ **Not thread-safe!** Don't share across threads without synchronization.

```python
# ❌ Don't do this
import threading

def worker():
    bus.publish(CreateOrder(...))  # Race condition!

threading.Thread(target=worker).start()
threading.Thread(target=worker).start()
```

### Performance

- **Subscribe:** O(1)
- **Publish:** O(n) where n = handlers for message type
- **Memory:** O(m) where m = total subscriptions

## InMemoryEventStore

In-memory implementation of the EventStore protocol.

```python
from orchestrix import InMemoryEventStore

store = InMemoryEventStore()
```

### Class Definition

```python
class InMemoryEventStore:
    """In-memory event store using defaultdict.
    
    Suitable for:
    - Development and testing
    - Proof of concepts
    - Single-process applications
    
    Characteristics:
    - Events stored in memory only
    - No persistence between restarts
    - Append-only semantics
    - Events returned in insertion order
    """
    
    def __init__(self) -> None:
        """Initialize empty event store."""
```

### Methods

#### `save(aggregate_id, events)`

Append events to aggregate's event stream.

**Parameters:**

- `aggregate_id` (str): Unique identifier for the aggregate
- `events` (list[Event]): Events to append

**Returns:** None

**Example:**

```python
events = [
    OrderCreated(order_id="ORD-001", customer_id="CUST-123"),
    ItemAdded(order_id="ORD-001", item={"sku": "A", "qty": 2}),
    OrderPaid(order_id="ORD-001", payment_id="PAY-001")
]

store.save("ORD-001", events)
```

**Append-Only:**

```python
# First save
store.save("ORD-001", [OrderCreated(...)])

# Second save - appends, doesn't replace
store.save("ORD-001", [OrderPaid(...)])

# Load returns both
events = store.load("ORD-001")
# → [OrderCreated, OrderPaid]
```

#### `load(aggregate_id)`

Load all events for an aggregate in chronological order.

**Parameters:**

- `aggregate_id` (str): Unique identifier for the aggregate

**Returns:** list[Event]

**Example:**

```python
# Load all events
events = store.load("ORD-001")

for event in events:
    print(f"{event.timestamp}: {event.__class__.__name__}")

# Reconstruct aggregate
order = Order.from_events(events)
```

**Empty Stream:**

```python
# Load non-existent aggregate
events = store.load("DOES-NOT-EXIST")
# → [] (empty list, not error)
```

### Behavior

**Event Order:**

Events are returned in the order they were saved:

```python
store.save("ORD-001", [event1, event2])
store.save("ORD-001", [event3])

events = store.load("ORD-001")
# → [event1, event2, event3]  # Chronological order
```

**Isolation:**

Each aggregate has independent event stream:

```python
store.save("ORD-001", [event1, event2])
store.save("ORD-002", [event3, event4])

load("ORD-001")  # → [event1, event2]
load("ORD-002")  # → [event3, event4]
```

### Memory Management

⚠️ **All events kept in memory!** Consider for production:

```python
# ❌ Bad for production
for i in range(1_000_000):
    store.save(f"ORD-{i}", [OrderCreated(...)])
# Will use lots of memory!

# ✅ Use persistent store for production
store = PostgreSQLEventStore(connection_string)
```

### Thread Safety

⚠️ **Not thread-safe!** Don't share across threads.

### Performance

- **Save:** O(1) append
- **Load:** O(n) where n = events for aggregate
- **Memory:** O(e) where e = total events stored

### Limitations

❌ No persistence - data lost on restart  
❌ No concurrent access control  
❌ No event versioning  
❌ No optimistic locking  
❌ No snapshots  

For production, use:
- PostgreSQLEventStore
- SQLiteEventStore
- MongoDBEventStore

## Usage Example

Complete example with both components:

```python
from orchestrix import (
    Command,
    Event,
    CommandHandler,
    Module,
    InMemoryMessageBus,
    InMemoryEventStore,
)
from dataclasses import dataclass

# Messages
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_id: str

# Handler
class CreateOrderHandler(CommandHandler[CreateOrder]):
    def __init__(self, bus, store):
        self.bus = bus
        self.store = store
    
    def handle(self, command: CreateOrder) -> None:
        # Create event
        event = OrderCreated(
            order_id=command.order_id,
            customer_id=command.customer_id
        )
        
        # Save
        self.store.save(command.order_id, [event])
        
        # Publish
        self.bus.publish(event)

# Module
class OrderModule(Module):
    def register(self, bus, store) -> None:
        bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
        bus.subscribe(OrderCreated, lambda e: print(f"📦 Order {e.order_id} created"))

# Application
bus = InMemoryMessageBus()
store = InMemoryEventStore()

module = OrderModule()
module.register(bus, store)

# Execute
bus.publish(CreateOrder(order_id="ORD-001", customer_id="CUST-123"))

# Verify
events = store.load("ORD-001")
assert len(events) == 1
assert isinstance(events[0], OrderCreated)
```

## Next Steps

- [Core API](core.md) - Core abstractions
- [Message Bus Guide](../guide/message-bus.md) - Detailed patterns
- [Event Store Guide](../guide/event-store.md) - Persistence patterns
