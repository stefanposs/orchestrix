# Core Concepts

Orchestrix is built around several key concepts from **Domain-Driven Design (DDD)** and **Event Sourcing**.

## Messages

All communication in Orchestrix happens through **Messages**. Every message is:

- **Immutable** - Implemented with `@dataclass(frozen=True)`
- **CloudEvents-compatible** - Has `id`, `type`, `source`, and `timestamp`
- **Type-safe** - Full type annotations for IDE support

```python
from orchestrix import Message, Command, Event

# Base message - rarely used directly
@dataclass(frozen=True, kw_only=True)
class MyMessage(Message):
    data: str
```

## Commands

**Commands** represent an **intention to change state**. They:

- Express what you want to happen
- May be rejected (validation, business rules)
- Are handled by exactly one handler
- Use imperative naming (CreateOrder, CancelOrder)

```python
from orchestrix import Command

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_name: str
    total_amount: float
```

## Events

**Events** represent **facts that have occurred**. They:

- Express what has happened
- Cannot be rejected (they already happened)
- May be handled by zero or more handlers
- Use past-tense naming (OrderCreated, OrderCancelled)

```python
from orchestrix import Event

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str
    total_amount: float
```

## Aggregates

**Aggregates** are domain objects that:

- Enforce business rules
- Maintain consistency boundaries
- Emit events when state changes
- Are reconstructed from their event stream

```python
from dataclasses import dataclass, field

@dataclass
class Order:
    order_id: str
    customer_name: str
    total_amount: float
    status: str = "pending"
    _events: list[Event] = field(default_factory=list, repr=False)
    
    @classmethod
    def create(cls, order_id: str, customer_name: str, total_amount: float):
        order = cls(order_id, customer_name, total_amount)
        order._events.append(OrderCreated(
            order_id=order_id,
            customer_name=customer_name,
            total_amount=total_amount
        ))
        return order
    
    def cancel(self) -> None:
        if self.status != "pending":
            raise ValueError("Can only cancel pending orders")
        self.status = "cancelled"
        self._events.append(OrderCancelled(order_id=self.order_id))
    
    def collect_events(self) -> list[Event]:
        events = self._events.copy()
        self._events.clear()
        return events
```

## Message Bus

The **MessageBus** routes messages to their handlers:

```python
from orchestrix import MessageBus, InMemoryMessageBus

bus = InMemoryMessageBus()

# Subscribe handlers
bus.subscribe(CreateOrder, create_order_handler)
bus.subscribe(OrderCreated, send_confirmation_email)
bus.subscribe(OrderCreated, update_inventory)

# Publish messages
bus.publish(CreateOrder(...))
```

## Event Store

The **EventStore** persists events for aggregate reconstruction:

```python
from orchestrix import EventStore, InMemoryEventStore

store = InMemoryEventStore()

# Save events
events = [OrderCreated(...), OrderShipped(...)]
store.save("ORDER-123", events)

# Load events
all_events = store.load("ORDER-123")
# Reconstruct aggregate from events
```

## Modules

**Modules** encapsulate domain logic and wire handlers to the bus:

```python
from orchestrix import Module, MessageBus, EventStore

class OrderModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        # Register command handlers
        bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
        bus.subscribe(CancelOrder, CancelOrderHandler(bus, store))
        
        # Register event handlers (projections, side effects)
        bus.subscribe(OrderCreated, log_order_created)
        bus.subscribe(OrderCancelled, refund_payment)
```

## Command Handlers

**Command Handlers** process commands:

1. Load aggregate from event store (or create new)
2. Execute business logic on aggregate
3. Collect new events from aggregate
4. Save events to store
5. Publish events to bus

```python
from orchestrix import CommandHandler

class CreateOrderHandler(CommandHandler[CreateOrder]):
    def __init__(self, bus: MessageBus, store: EventStore) -> None:
        self.bus = bus
        self.store = store
    
    def handle(self, command: CreateOrder) -> None:
        # Create aggregate
        order = Order.create(
            command.order_id,
            command.customer_name,
            command.total_amount
        )
        
        # Persist and publish events
        events = order.collect_events()
        self.store.save(command.order_id, events)
        for event in events:
            self.bus.publish(event)
```

## Putting It Together

The typical flow is:

1. **Application** publishes a **Command** to the **MessageBus**
2. **MessageBus** routes to the appropriate **CommandHandler**
3. **CommandHandler** loads/creates an **Aggregate**
4. **Aggregate** executes business logic and emits **Events**
5. **Events** are saved to **EventStore**
6. **Events** are published to **MessageBus**
7. **Event Handlers** react to events (projections, notifications, etc.)

```
┌─────────────┐
│ Application │
└──────┬──────┘
       │ publish(Command)
       ▼
┌─────────────┐
│ MessageBus  │
└──────┬──────┘
       │ route
       ▼
┌────────────────┐      ┌───────────┐
│ CommandHandler │─────▶│ Aggregate │
└────────┬───────┘      └─────┬─────┘
         │                     │ emit Events
         │                     ▼
         │              ┌──────────────┐
         │              │ collect      │
         │              │ _events      │
         │              └──────┬───────┘
         ▼                     │
┌────────────────┐             │
│ EventStore     │◀────────────┘
│ save(events)   │
└────────────────┘
         │
         │ publish Events
         ▼
┌─────────────────┐
│ Event Handlers  │
│ (projections,   │
│  side effects)  │
└─────────────────┘
```

## Next Steps

- [Creating Modules](../guide/creating-modules.md) - Module design patterns
- [Commands & Events](../guide/commands-events.md) - Message design guidelines
