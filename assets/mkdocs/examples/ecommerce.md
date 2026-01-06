# E-Commerce: Order Processing with Sagas

This example demonstrates a complete order processing workflow using multi-aggregate sagas, compensation logic, and async event handlers.

> **📂 Source Code:**  
> Complete Example: [`examples/ecommerce/`](https://github.com/stefanposs/orchestrix/tree/main/examples/ecommerce)  
> Main Demo: [`examples/ecommerce/example.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/ecommerce/example.py)  
> Domain Models: [`examples/ecommerce/models.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/ecommerce/models.py)

## Overview

The e-commerce example demonstrates:

- ✅ **Order State Machine** - Manages order lifecycle
- ✅ **Multi-Aggregate Saga** - Coordinates Order → Payment → Inventory
- ✅ **Compensation Logic** - Automatic rollback on failure
- ✅ **Async Event Handlers** - Notification processing
- ✅ **Distributed Transactions** - Across multiple aggregates

## Quick Start

```bash
# Run the e-commerce example
uv run python -m examples.ecommerce.example
```

## Architecture

The order saga coordinates a distributed workflow across multiple aggregates:

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
OrderConfirmed Event ✅
```

### Compensation Flow

If any step fails, the saga automatically compensates:

```
InventoryReservationFailed Event → OrderSaga
    ↓
RefundPayment Command
    ↓
PaymentRefunded Event
    ↓
CancelOrder Command
    ↓
OrderCancelled Event → Release Inventory ❌
```

## Domain Model

### Commands

#### CreateOrder
```python
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str
    items: list[OrderItem]
    shipping_address: Address

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: Decimal

@dataclass
class Address:
    street: str
    city: str
    state: str
    postal_code: str
    country: str
```

#### ProcessPayment
```python
@dataclass(frozen=True, kw_only=True)
class ProcessPayment(Command):
    order_id: str
    amount: Decimal
    payment_method: str  # "credit_card", "paypal", etc.
```

#### ReserveInventory
```python
@dataclass(frozen=True, kw_only=True)
class ReserveInventory(Command):
    order_id: str
    items: list[OrderItem]
```

### Events

**Order Events:**
- `OrderCreated` - Order created by customer
- `OrderConfirmed` - Payment and inventory successful
- `OrderCancelled` - Order cancelled or compensation executed
- `OrderShipped` - Order dispatched to customer

**Payment Events:**
- `PaymentProcessing` - Payment initiated
- `PaymentCompleted` - Payment successful
- `PaymentFailed` - Payment rejected
- `PaymentRefunded` - Payment compensated

**Inventory Events:**
- `InventoryReserved` - Items reserved for order
- `InventoryReservationFailed` - Not enough stock
- `InventoryReleased` - Reservation cancelled

### Aggregate

#### Order
```python
@dataclass
class Order:
    order_id: str
    customer_id: str
    items: list[OrderItem]
    status: OrderStatus  # State machine
    total_amount: Decimal
    payment_id: Optional[str] = None
    reservation_id: Optional[str] = None
    
    def create(self, ...):
        # Emit OrderCreated
    
    def complete_payment(self, payment_id: str):
        # Emit PaymentCompleted
    
    def reserve_inventory(self, reservation_id: str):
        # Emit InventoryReserved
    
    def confirm(self):
        # Emit OrderConfirmed
```

## Key Patterns

### 1. State Machine

The Order aggregate uses a state machine to ensure valid transitions:

```python
class OrderStatus(str, Enum):
    PENDING = "pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_COMPLETED = "payment_completed"
    INVENTORY_RESERVED = "inventory_reserved"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

# Valid transitions
transitions = {
    PENDING: [PAYMENT_PROCESSING, CANCELLED],
    PAYMENT_PROCESSING: [PAYMENT_COMPLETED, CANCELLED],
    PAYMENT_COMPLETED: [INVENTORY_RESERVED, CANCELLED],
    INVENTORY_RESERVED: [CONFIRMED, CANCELLED],
}
```

### 2. Saga Coordinator

The OrderSaga listens to events and coordinates the workflow:

```python
class OrderSaga:
    async def on_order_created(self, event: OrderCreated):
        # Step 1: Process payment
        await self.bus.send(ProcessPayment(
            order_id=event.order_id,
            amount=event.total_amount,
            payment_method="credit_card",
        ))
    
    async def on_payment_completed(self, event: PaymentCompleted):
        # Step 2: Reserve inventory
        await self.bus.send(ReserveInventory(
            order_id=event.order_id,
            items=event.items,
        ))
    
    async def on_inventory_reserved(self, event: InventoryReserved):
        # Step 3: Confirm order
        await self.bus.send(ConfirmOrder(
            order_id=event.order_id,
        ))
    
    async def on_inventory_failed(self, event: InventoryReservationFailed):
        # Compensation: Refund payment
        await self.bus.send(RefundPayment(
            order_id=event.order_id,
        ))
```

### 3. Command Handlers

Separate command handlers isolate business logic:

```python
async def handle_create_order(
    command: CreateOrder,
    repository: AggregateRepository,
):
    # Create order aggregate
    order = Order()
    order.create(
        order_id=command.order_id,
        customer_id=command.customer_id,
        items=command.items,
        shipping_address=command.shipping_address,
    )
    
    # Save and publish events
    await repository.save_async(order)
```

### 4. Compensation

Saga automatically handles failures with compensation:

```python
async def on_payment_failed(self, event: PaymentFailed):
    # Cancel order
    await self.bus.send(CancelOrder(
        order_id=event.order_id,
        reason="Payment failed",
    ))

async def on_inventory_failed(self, event: InventoryReservationFailed):
    # Step 1: Refund payment
    await self.bus.send(RefundPayment(
        order_id=event.order_id,
    ))
    
    # Step 2: Release inventory (if partially reserved)
    await self.bus.send(ReleaseInventory(
        order_id=event.order_id,
    ))
    
    # Step 3: Cancel order
    await self.bus.send(CancelOrder(
        order_id=event.order_id,
        reason="Inventory unavailable",
    ))
```

## Usage Example

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
    await message_bus.publish_async(
        CreateOrder(
            order_id=order_id,
            customer_id="customer-456",
            items=[
                OrderItem(
                    product_id="laptop-x1",
                    quantity=1,
                    unit_price=Decimal("1299.99"),
                ),
                OrderItem(
                    product_id="mouse-m2",
                    quantity=2,
                    unit_price=Decimal("29.99"),
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
    )

    # Wait for saga to complete
    await asyncio.sleep(0.5)

    # Load order to check final state
    order = await repository.load_async(Order, order_id)
    print(f"Order Status: {order.status}")
    print(f"Total Amount: ${order.total_amount}")
    print(f"Payment ID: {order.payment_id}")
    print(f"Reservation ID: {order.reservation_id}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

### Test Successful Order

```python
async def test_successful_order():
    # Setup
    event_store = InMemoryEventStore()
    repository = AggregateRepository(event_store)

    # Create order
    order = Order()
    order.create(
        order_id="test-123",
        customer_id="customer-456",
        items=[...],
        shipping_address=Address(...),
    )

    await repository.save_async(order)

    # Verify initial state
    loaded = await repository.load_async(Order, "test-123")
    assert loaded.status == OrderStatus.PENDING
    assert loaded.customer_id == "customer-456"
```

### Test Payment Failure

```python
async def test_payment_failure():
    # Setup with failing payment
    payment_service = MockPaymentService(should_fail=True)
    
    # Create order
    await message_bus.publish_async(CreateOrder(...))
    await asyncio.sleep(0.1)
    
    # Verify order was cancelled
    order = await repository.load_async(Order, order_id)
    assert order.status == OrderStatus.CANCELLED
```

### Test Inventory Failure

```python
async def test_inventory_failure_compensation():
    # Setup with insufficient stock
    inventory_service = MockInventoryService(available_stock=0)
    
    # Create order
    await message_bus.publish_async(CreateOrder(...))
    await asyncio.sleep(0.1)
    
    # Verify compensation executed
    order = await repository.load_async(Order, order_id)
    assert order.status == OrderStatus.CANCELLED
    
    # Verify payment was refunded
    assert payment_service.refunded_payments[order_id]
```

## Extending the Example

### Add Payment Gateway Integration

```python
from payment_gateway import PaymentGateway

class RealPaymentHandler:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway

    async def handle_process_payment(self, command: ProcessPayment):
        order = await repository.load_async(Order, command.order_id)
        
        try:
            result = await self.gateway.charge(
                amount=command.amount,
                method=command.payment_method,
                customer_id=order.customer_id,
            )
            
            order.complete_payment(payment_id=result.transaction_id)
            await repository.save_async(order)
            
        except PaymentGatewayError as e:
            order.fail_payment(reason=str(e))
            await repository.save_async(order)
```

### Add Inventory Service

```python
from inventory_service import InventoryClient

class RealInventoryHandler:
    def __init__(self, client: InventoryClient):
        self.client = client

    async def handle_reserve_inventory(self, command: ReserveInventory):
        order = await repository.load_async(Order, command.order_id)
        
        try:
            reservation = await self.client.reserve(
                items=[(item.product_id, item.quantity) 
                       for item in command.items]
            )
            
            order.reserve_inventory(reservation_id=reservation.id)
            await repository.save_async(order)
            
        except OutOfStockError as e:
            order.fail_inventory_reservation(reason=str(e))
            await repository.save_async(order)
```

## Production Considerations

### 1. Idempotency

Add command deduplication to prevent double-processing:

```python
processed_commands = set()

async def handle_command(command: Command):
    command_id = f"{command.type}:{command.order_id}"
    
    if command_id in processed_commands:
        return  # Already processed
    
    # Process command
    await process(command)
    
    processed_commands.add(command_id)
```

### 2. Timeouts

Add saga timeout logic for hanging workflows:

```python
class OrderSaga:
    timeout: timedelta = timedelta(minutes=10)
    
    async def check_timeouts(self):
        for order_id, created_at in self.pending_orders.items():
            if datetime.now() - created_at > self.timeout:
                await self.cancel_order(order_id, "Timeout")
```

### 3. Monitoring

Track saga progress and failure rates:

```python
metrics = {
    "orders_created": Counter(),
    "orders_confirmed": Counter(),
    "orders_cancelled": Counter(),
    "payment_failures": Counter(),
    "inventory_failures": Counter(),
    "avg_order_duration": Histogram(),
}
```

### 4. Dead Letter Queue

Handle permanent failures:

```python
class OrderSaga:
    dead_letter_queue: list = []
    max_retries: int = 3
    
    async def handle_permanent_failure(self, order_id: str, reason: str):
        self.dead_letter_queue.append({
            "order_id": order_id,
            "reason": reason,
            "timestamp": datetime.now(),
        })
        
        # Alert operations team
        await send_alert(f"Order {order_id} moved to DLQ: {reason}")
```

### 5. Compensation Limits

Define max retry attempts for compensations:

```python
async def compensate_payment(self, order_id: str, attempt: int = 1):
    if attempt > 3:
        # Move to manual review
        await self.escalate_to_manual_review(order_id)
        return
    
    try:
        await self.bus.send(RefundPayment(order_id=order_id))
    except RefundError:
        # Retry with exponential backoff
        await asyncio.sleep(2 ** attempt)
        await self.compensate_payment(order_id, attempt + 1)
```

## Related Examples

- **[Banking](banking.md)** - Saga pattern with money transfers
- **[Notifications](notifications.md)** - Async event handlers
- **[Lakehouse GDPR](lakehouse-gdpr.md)** - Event sourcing patterns

## Learn More

- [Saga Pattern Guide](../guide/best-practices.md#sagas)
- [State Machines](../guide/best-practices.md#state-machines)
- [Testing Sagas](../development/testing.md)

## Source Code

- [`aggregate.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/ecommerce/aggregate.py) - Order aggregate with state machine
- [`saga.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/ecommerce/saga.py) - Order saga coordinator
- [`handlers.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/ecommerce/handlers.py) - Command and event handlers
- [`models.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/ecommerce/models.py) - Commands, events, and value objects

[**Browse Complete Example →**](https://github.com/stefanposs/orchestrix/tree/main/examples/ecommerce)
