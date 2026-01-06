# E-Commerce Demo

This example demonstrates a complete order processing workflow using Orchestrix:

1. **Order Aggregate**: State machine managing order lifecycle
2. **Multi-Aggregate Saga**: Coordinates Order → Payment → Inventory flow
3. **Compensation Logic**: Automatic rollback when steps fail
4. **Event Handlers**: Async notification processing

## Architecture

```
CreateOrder Command
    ↓
OrderAggregate.create()
    ↓
OrderCreated Event → OrderSaga
    ↓
ProcessPayment Command
    ↓
PaymentCompleted Event → OrderSaga
    ↓
ReserveInventory Command
    ↓
InventoryReserved Event → OrderSaga
    ↓
ConfirmOrder Command
    ↓
OrderConfirmed Event
```

## Compensation Flow

If inventory reservation fails:
```
InventoryReservationFailed Event → OrderSaga
    ↓
RefundPayment Command
    ↓
PaymentRefunded Event
    ↓
CancelOrder Command
    ↓
OrderCancelled Event → Release Inventory
```

## Usage

```python
import asyncio
from decimal import Decimal

from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus

from examples.ecommerce.aggregate import Order
from examples.ecommerce.handlers import register_handlers
from examples.ecommerce.models import Address, CreateOrder, OrderItem
from examples.ecommerce.saga import register_saga


async def main():
    # Setup infrastructure
    event_store = InMemoryEventStore()
    message_bus = InMemoryMessageBus()
    repository = AggregateRepository(event_store)

    # Register handlers and saga
    register_handlers(message_bus, repository)
    register_saga(message_bus, repository)

    # Create an order
    order_id = "order-123"
    command = CreateOrder(
        order_id=order_id,
        customer_id="customer-456",
        items=[
            OrderItem(
                product_id="product-789",
                quantity=2,
                unit_price=Decimal("29.99"),
            ),
            OrderItem(
                product_id="product-101",
                quantity=1,
                unit_price=Decimal("49.99"),
            ),
        ],
        shipping_address=Address(
            street="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA",
        ),
    )

    # Publish command (triggers saga)
    await message_bus.publish_async(command)

    # Give saga time to process
    await asyncio.sleep(0.1)

    # Load order to check final state
    order = await repository.load_async(Order, order_id)
    print(f"Order Status: {order.status}")
    print(f"Payment ID: {order.payment_id}")
    print(f"Reservation ID: {order.reservation_id}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Patterns

### 1. State Machine
The Order aggregate uses a state machine to ensure valid transitions:
- PENDING → PAYMENT_PROCESSING → PAYMENT_COMPLETED → INVENTORY_RESERVED → CONFIRMED

### 2. Saga Coordinator
The OrderSaga listens to events and coordinates the workflow:
- Reacts to events from multiple aggregates
- Triggers compensating actions on failure
- Maintains workflow state implicitly through events

### 3. Command Handlers
Separate command handlers isolate business logic:
- Load aggregates
- Execute business methods
- Save aggregates
- Publish resulting events

### 4. Compensation
Saga automatically handles failures:
- Payment failed → Cancel order
- Inventory failed → Refund payment → Release inventory → Cancel order

## Testing

```python
async def test_successful_order():
    event_store = InMemoryEventStore()
    repository = AggregateRepository(event_store)

    order = Order()
    order.create(
        order_id="test-123",
        customer_id="customer-456",
        items=[...],
        shipping_address=Address(...),
    )

    await repository.save_async(order)

    # Verify state
    loaded = await repository.load_async(Order, "test-123")
    assert loaded.status == OrderStatus.PENDING
```

## Extending the Example

**Add Payment Gateway Integration:**
```python
from payment_gateway import PaymentGateway

class RealPaymentHandler:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway

    async def handle_process_payment(self, command: ProcessPayment):
        result = await self.gateway.charge(
            amount=command.amount,
            method=command.method,
        )
        if result.success:
            order.complete_payment(...)
        else:
            order.fail_payment(result.reason)
```

**Add Inventory Service:**
```python
from inventory_service import InventoryClient

class RealInventoryHandler:
    def __init__(self, client: InventoryClient):
        self.client = client

    async def handle_reserve_inventory(self, command: ReserveInventory):
        try:
            reservation = await self.client.reserve(command.items)
            order.reserve_inventory(
                items=command.items,
                reservation_id=reservation.id,
            )
        except OutOfStockError as e:
            order.fail_inventory_reservation(
                items=command.items,
                reason=str(e),
            )
```

## Production Considerations

1. **Idempotency**: Add command deduplication to prevent double-processing
2. **Timeouts**: Add saga timeout logic for hanging workflows
3. **Monitoring**: Track saga progress and failure rates
4. **Dead Letter Queue**: Handle permanent failures
5. **Compensation Limits**: Define max retry attempts
"""
