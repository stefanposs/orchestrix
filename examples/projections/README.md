# CQRS Projections Example

This example demonstrates how to use the **ProjectionEngine** to build read models from an event stream, implementing the CQRS (Command Query Responsibility Segregation) pattern.

## Overview

Projections are a key pattern in event sourcing that:

1. **Consume events** from the event stream
2. **Build read models** optimized for queries (denormalized views)
3. **Provide fast queries** by pre-computing aggregations
4. **Enable eventual consistency** between write and read sides

## Key Concepts

### Event Sourcing vs CQRS

- **Event Sourcing**: Stores state changes as immutable events
- **CQRS**: Separates command handling (mutations) from query handling (reads)
- **Projections**: Bridge between event stream and read models

### OrderSummary Read Model

The example builds an `OrderSummary` read model from domain events:

```
Events Stream:
  OrderCreated → ItemAdded → ItemAdded → OrderConfirmed → OrderShipped → OrderDelivered

Read Model (OrderSummary):
  {
    order_id: "ORDER-001",
    status: "delivered",
    customer_name: "Alice Johnson",
    items: [
      {item_name: "Keyboard", quantity: 1, unit_price: 79.99},
      {item_name: "Mouse", quantity: 1, unit_price: 39.99}
    ],
    total_amount: 269.97,
    carrier: "FedEx",
    tracking_number: "1234567890"
  }
```

## Projection Architecture

### ProjectionEngine

The core engine handles:

- **Event Handler Registration**: Register handlers for each event type
- **Event Processing**: Route events to appropriate handlers
- **State Tracking**: Track which events have been processed (for recovery)
- **Error Handling**: Manage projection failures and recovery
- **Health Status**: Monitor projection health and errors

### ProjectionState

Tracks projection progress:

```python
@dataclass
class ProjectionState:
    projection_id: str                          # Unique ID
    last_processed_event_id: Optional[str]      # For idempotency
    last_processed_position: int                # Event stream position
    error_count: int                            # Number of errors
    is_healthy: bool                            # Health status
```

### Handler Registration

Register handlers using the decorator pattern:

```python
engine = ProjectionEngine("order-summary", state_store)

@engine.on(OrderCreated)
async def on_order_created(event: OrderCreated) -> None:
    # Build read model from event
    order_summary = OrderSummary(
        order_id=event.order_id,
        customer_name=event.customer_name
    )
    save_to_database(order_summary)

@engine.on(ItemAddedToOrder)
async def on_item_added(event: ItemAddedToOrder) -> None:
    # Update existing read model
    order = load_from_database(event.order_id)
    order.add_item(ItemData(...))
    save_to_database(order)
```

## Running the Example

```bash
# Run the projection example
python -m examples.projections.example
```

### Expected Output

```
============================================================
CQRS Projection Example: Order Read Models
============================================================

Processing events...

✓ Order created: ORDER-001 for Alice Johnson
  ✓ Item added: Wireless Keyboard (x1 @ $79.99)
  ✓ Item added: Mouse (x1 @ $39.99)
✓ Order confirmed
✓ Order shipped via FedEx (1234567890)
✓ Order delivered

============================================================
Querying Read Models
============================================================

============================================================
Order Summary: ORDER-001
============================================================
Customer: Alice Johnson (CUST-001)
Status: DELIVERED

Items:
  Wireless Keyboard x1 @ $79.99 = $79.99
  Mouse x1 @ $39.99 = $39.99

Total: $269.97
Shipping: FedEx (Tracking: 1234567890)
============================================================
```

## Key Features

### 1. Decorator-Based Handler Registration

```python
@engine.on(OrderCreated)
async def handler(event: OrderCreated) -> None:
    # Async and sync handlers both supported
    pass
```

### 2. Idempotent Processing

Projections track processed events to ensure exactly-once semantics:

```python
if last_processed_event_id == event.id:
    return  # Already processed, skip
```

### 3. Error Handling

Projection health is monitored:

```python
if engine.is_healthy():
    # Projection is healthy
else:
    # Projection encountered errors, may need recovery
```

### 4. Event Replay

Rebuild read models from scratch:

```python
# Replay all events to rebuild read models
await engine.replay(all_events)
```

### 5. State Persistence

Projection state is persisted for recovery:

```python
state_store = InMemoryProjectionStateStore()  # Or database implementation
await state_store.save_state(projection_state)
```

## Common Patterns

### Multiple Handlers Per Event

```python
@engine.on(OrderCreated)
async def handler1(event: OrderCreated) -> None:
    # Update order summary
    pass

@engine.on(OrderCreated)
async def handler2(event: OrderCreated) -> None:
    # Update order index
    pass
```

Both handlers will be called for each `OrderCreated` event.

### Querying Read Models

```python
# Fast queries on read model
order = read_model_db.get_by_id("ORDER-001")
orders_by_status = read_model_db.query_by_status("shipped")
customer_orders = read_model_db.query_by_customer("CUST-001")
```

### Handling Event Failures

```python
try:
    await engine.handle_event(event)
except Exception as e:
    logger.error(f"Projection failed: {e}")
    # Implement retry logic or dead letter handling
```

## Performance Considerations

### Single-Threaded Processing

Events are processed sequentially to maintain ordering:

```python
for event in event_stream:
    await engine.handle_event(event)
```

### Batch Processing

Process multiple events efficiently:

```python
await engine.process_events(events_batch)
```

### Read Model Optimization

Keep read models denormalized for fast queries:

- Pre-compute aggregations
- Index frequently queried fields
- Avoid joins in queries

## State Management

### ProjectionStateStore Interface

Implement for persistent state storage:

```python
class ProjectionStateStore(Protocol):
    async def load_state(self, projection_id: str) -> Optional[ProjectionState]:
        ...
    
    async def save_state(self, state: ProjectionState) -> None:
        ...
```

### In-Memory vs Persistent

- **In-Memory**: Fast, good for testing
- **Database**: Durable, required for production

## Testing

Full test coverage included:

```bash
pytest tests/test_projection_engine.py -v
```

Tests cover:

- Handler registration
- Event processing
- Idempotency
- State persistence
- Error handling
- Projection replay
- Concurrent processing

## Production Checklist

- [ ] Implement persistent `ProjectionStateStore` (PostgreSQL, etc.)
- [ ] Add monitoring/alerting for projection health
- [ ] Implement dead letter queue for failed events
- [ ] Handle projection rebuild/reset scenarios
- [ ] Add backpressure handling for high event volume
- [ ] Implement eventual consistency guarantees
- [ ] Test disaster recovery procedures

## Related Concepts

- **CQRS**: Command Query Responsibility Segregation
- **Event Sourcing**: Storing state as immutable events
- **Eventual Consistency**: Read models may lag behind events
- **Read Models**: Denormalized views optimized for queries
- **Event Stream**: Ordered sequence of domain events

## References

- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Orchestrix Documentation](../../docs/)
