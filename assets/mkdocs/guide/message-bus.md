
# Message Bus

Route commands and events to handlers using the message bus.

## Protocols

```python
# Sync
class MessageBus(Protocol):
    def publish(self, message: Message) -> None: ...
    def subscribe(self, message_type: type[T], handler: Callable[[T], None]) -> None: ...

# Async
class AsyncMessageBus(Protocol):
    async def publish(self, message: Message) -> None: ...
    def subscribe(self, message_type: type[T], handler: Callable[[T], Coroutine]) -> None: ...
```

## Implementations

### InMemoryMessageBus (sync)

```python
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus

bus = InMemoryMessageBus()
bus.subscribe(OrderCreated, lambda e: print(f"Order: {e.order_id}"))
bus.publish(OrderCreated(order_id="123", customer_name="Alice", total_amount=99.0))
```

### InMemoryAsyncMessageBus (async)

```python
from orchestrix.infrastructure.memory.async_bus import InMemoryAsyncMessageBus

bus = InMemoryAsyncMessageBus()
bus.subscribe(OrderCreated, my_async_handler)
await bus.publish(OrderCreated(...))
```

### GCP Pub/Sub

```python
from orchestrix.infrastructure.gcp_pubsub import GCPPubSub

bus = GCPPubSub(project_id="my-project", topic_id="events")
```

## Handler Registration

Subscribe handlers per message type:

```python
bus.subscribe(CreateOrder, handle_create_order)    # command → 1 handler
bus.subscribe(OrderCreated, send_email)            # event → multiple handlers
bus.subscribe(OrderCreated, update_projection)
```

## Error Handling

The sync `InMemoryMessageBus` catches handler exceptions and continues
to the next handler. Exceptions are logged, not re-raised. This prevents
a failing side-effect handler from blocking the main flow.

For explicit error handling, wrap handlers:

```python
def safe_handler(event: OrderCreated):
    try:
        send_email(event)
    except Exception:
        logger.exception("Email failed for %s", event.order_id)

bus.subscribe(OrderCreated, safe_handler)
```

## Publishing Events from Aggregates

The typical pattern uses `AggregateRepository.save()` which persists events.
Publish events separately if you need bus-based side-effects:

```python
class MyHandler:
    def handle(self, cmd: CreateOrder):
        order = Order()
        order.create(cmd)
        self.repo.save(order)

        # Optionally publish to bus for side-effects
        for event in order.uncommitted_events:
            self.bus.publish(event)
        order.mark_events_committed()
```

## Best Practices

1. **Commands → one handler**, Events → many handlers
2. **Don't put business logic in event handlers** — keep it in aggregates
3. **Use async bus for I/O-heavy handlers** (email, HTTP, database)
4. **Consider idempotency** — handlers may be called more than once
