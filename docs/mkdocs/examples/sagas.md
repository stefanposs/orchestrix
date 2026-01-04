# Sagas - Long-Running Business Processes

Sagas coordinate long-running business processes across multiple aggregates with automatic compensation on failure.

## Overview

A saga is a sequence of local transactions where each transaction updates data within a single service. If a step fails, the saga executes compensating transactions to undo the changes made by previous steps.

## Key Features

- **Compensation Logic** - Automatic rollback on failure
- **State Management** - Tracks saga progress
- **Event-Driven** - Reacts to domain events
- **Type-Safe** - Full type annotations

## Basic Example

```python
from orchestrix.core.saga import Saga, SagaStep
from orchestrix.core.message import Event
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    amount: float

@dataclass(frozen=True)
class PaymentProcessed(Event):
    order_id: str
    payment_id: str

@dataclass(frozen=True)
class InventoryReserved(Event):
    order_id: str
    items: list[str]

# Define saga
class OrderSaga(Saga):
    def __init__(self):
        super().__init__()
        self.add_step(
            SagaStep(
                action=self.process_payment,
                compensation=self.refund_payment
            )
        )
        self.add_step(
            SagaStep(
                action=self.reserve_inventory,
                compensation=self.release_inventory
            )
        )
    
    async def process_payment(self, order: OrderCreated):
        # Process payment
        return PaymentProcessed(
            order_id=order.order_id,
            payment_id="pay-123"
        )
    
    async def refund_payment(self, payment: PaymentProcessed):
        # Refund on failure
        pass
    
    async def reserve_inventory(self, payment: PaymentProcessed):
        # Reserve inventory
        return InventoryReserved(
            order_id=payment.order_id,
            items=["item-1", "item-2"]
        )
    
    async def release_inventory(self, inventory: InventoryReserved):
        # Release on failure
        pass
```

## Running the Example

```bash
cd examples/sagas
uv run example.py
```

## Use Cases

- **Distributed Transactions** - Coordinate changes across multiple aggregates
- **Order Processing** - Payment, inventory, shipping coordination
- **Travel Booking** - Flight + hotel + car rental
- **Account Transfers** - Debit one account, credit another

## Best Practices

1. **Idempotency** - Saga steps should be idempotent
2. **Compensation Order** - Reverse order of execution
3. **State Persistence** - Store saga state for recovery
4. **Timeout Handling** - Handle long-running operations

## Learn More

- [Best Practices](../guide/best-practices.md)
- [Full Example](https://github.com/stefanposs/orchestrix/tree/main/examples/sagas)
- [API Reference](../api/core.md#saga)
