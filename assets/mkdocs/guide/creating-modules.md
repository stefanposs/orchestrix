
# Creating Modules

Modules encapsulate domain logic and wire handlers to infrastructure.

## The Module Protocol

```python
from orchestrix.core.common.module import Module

class OrderModule:
    """Satisfies the Module protocol."""

    def register(self, bus, store):
        handler = OrderCommandHandler(bus, store)
        bus.subscribe(CreateOrder, handler.handle_create)
        bus.subscribe(CancelOrder, handler.handle_cancel)

        # Event handlers for side-effects
        bus.subscribe(OrderCreated, self._log_order)
```

The `Module` protocol requires a single method:

```python
class Module(Protocol):
    def register(self, bus: MessageBus, store: EventStore) -> None: ...
```

## Module Structure

Follow the Polylith convention:

```
bases/orchestrix/my_demo/
├── __init__.py       # Package marker + exports
├── models.py         # Commands and Events
├── aggregate.py      # Aggregate roots
├── handlers.py       # Command handlers
├── saga.py           # Saga orchestration (optional)
└── main.py           # Runnable entry point
```

## Command Handler Pattern

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore

class OrderCommandHandler:
    def __init__(self, bus, store):
        self.bus = bus
        self.repo = AggregateRepository(event_store=store)

    def handle_create(self, cmd: CreateOrder):
        order = Order()
        order.create(cmd)
        self.repo.save(order)

    def handle_cancel(self, cmd: CancelOrder):
        order = self.repo.load(Order, cmd.order_id)
        order.cancel(cmd)
        self.repo.save(order)
```

## Wiring

```python
from orchestrix.infrastructure.memory.store import InMemoryEventStore
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus

store = InMemoryEventStore()
bus = InMemoryMessageBus()

module = OrderModule()
module.register(bus, store)

# Now use bus.publish(CreateOrder(...))
```

## Best Practices

1. **One module per bounded context** — keep modules focused
2. **Inject dependencies** — pass `bus` and `store`, don't import globals
3. **Keep handlers thin** — delegate to the aggregate
4. **Use type annotations** — improves IDE support and documentation
5. **Test modules in isolation** — use `InMemoryEventStore` for fast tests
