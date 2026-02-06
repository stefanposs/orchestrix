
# Best Practices

Guidelines for building robust Orchestrix applications.

## Aggregate Design

1. **Keep aggregates small** — one consistency boundary per aggregate
2. **No external I/O in aggregates** — aggregates are pure domain logic
3. **Use `_when_<event>` methods** — convention-based state mutation
4. **Validate in commands** — reject bad data before it reaches the aggregate
5. **Emit events, don't return values** — the event is the result

```python
@dataclass
class Order(AggregateRoot):
    def create(self, cmd: CreateOrder):
        # Validate
        if cmd.total_amount <= 0:
            raise ValueError("Amount must be positive")
        # Emit event
        self._apply_event(OrderCreated(
            order_id=cmd.order_id,
            total_amount=cmd.total_amount,
        ))

    def _when_order_created(self, event: OrderCreated):
        self.aggregate_id = event.order_id
        self.total_amount = event.total_amount
```

## Event Design

1. **Events are immutable facts** — never modify stored events
2. **Use past-tense naming** — `OrderCreated`, not `CreateOrder`
3. **Include all relevant data** — events should be self-describing
4. **Version events** — add new fields with defaults, never remove fields
5. **Keep events small** — only what changed, not full state

## Command Design

1. **Use imperative naming** — `CreateOrder`, `SuspendAccount`
2. **Validate early** — use `__post_init__` with built-in validators
3. **One handler per command** — commands have exactly one receiver
4. **Keep commands thin** — just the data needed to execute

## Saga Patterns

1. **Define compensation for every step** — what happens on failure?
2. **Use `SagaStep` with explicit compensation**:

```python
from orchestrix.core.execution.saga import Saga, SagaStep, InMemorySagaStateStore

saga = Saga(
    saga_type="OrderSaga",
    steps=[
        SagaStep(name="payment", action=process_payment, compensation=refund_payment),
        SagaStep(name="inventory", action=reserve_stock, compensation=release_stock),
        SagaStep(name="confirm", action=confirm_order),
    ],
    state_store=InMemorySagaStateStore(),
)
await saga.execute(order_id="123", amount=99.0)
```

3. **Check saga state** — `saga.is_completed()`, `saga.is_successful()`
4. **Handle timeouts** — sagas should not hang indefinitely

## Error Handling

1. **Use specific exceptions**:
    - `ValidationError` for invalid input
    - `ConcurrencyError` for version conflicts
    - `HandlerError` for handler failures
2. **Retry transient failures** with `ExponentialBackoff` or `FixedDelay`
3. **Dead letter queue** for permanent failures

## Testing

1. **Test aggregates in isolation** — no infrastructure needed
2. **Use `InMemoryEventStore`** for integration tests
3. **Test saga compensation** — force failures and verify rollback
4. **Test event replay** — rebuild aggregate and assert state
5. **Test validation** — ensure bad commands are rejected

```python
def test_order_creation():
    order = Order()
    order.create(CreateOrder(order_id="1", total_amount=99.0))
    assert order.aggregate_id == "1"
    assert len(order.uncommitted_events) == 1

def test_invalid_amount():
    order = Order()
    with pytest.raises(ValueError):
        order.create(CreateOrder(order_id="1", total_amount=-5.0))
```

## Performance

1. **Use snapshots** for aggregates with > 100 events
2. **Use async stores and buses** for I/O-heavy workloads
3. **Size connection pools** based on expected concurrency
4. **Index by aggregate_id** (handled by `PostgreSQLEventStore`)
