"""Order processing saga coordinator.

This saga coordinates the multi-aggregate workflow:
1. Create Order → 2. Process Payment → 3. Reserve Inventory → 4. Confirm Order

If any step fails, compensation actions are triggered:
- Payment failed → Cancel Order
- Inventory failed → Refund Payment → Cancel Order
"""
from dataclasses import dataclass
from uuid import uuid4

from orchestrix.core.aggregate import AggregateRepository
from orchestrix.core.event import Event
from orchestrix.core.messaging import MessageBus

from .aggregate import Order
from .models import (
    CancelOrder,
    ConfirmOrder,
    InventoryReservationFailed,
    InventoryReserved,
    OrderCancelled,
    OrderCreated,
    PaymentCompleted,
    PaymentFailed,
    ProcessPayment,
    RefundPayment,
    ReleaseInventory,
    ReserveInventory,
)


@dataclass
class OrderSaga:
    """Saga coordinating the order processing workflow."""

    message_bus: MessageBus
    repository: AggregateRepository

    async def handle_order_created(self, event: Event) -> None:
        """Start saga when order is created."""
        data: OrderCreated = event.data

        # Calculate total amount
        total = sum(item.total_price for item in data.items)

        # Initiate payment
        payment_id = str(uuid4())
        await self.message_bus.publish_async(
            ProcessPayment(
                order_id=data.order_id,
                payment_id=payment_id,
                amount=total,
                method="credit_card",  # Default method
            )
        )

    async def handle_payment_completed(self, event: Event) -> None:
        """Continue saga after payment succeeds."""
        data: PaymentCompleted = event.data

        # Load order to get items
        order = await self.repository.load_async(Order, data.order_id)

        # Reserve inventory
        await self.message_bus.publish_async(
            ReserveInventory(
                order_id=data.order_id,
                items=order.items,
            )
        )

    async def handle_payment_failed(self, event: Event) -> None:
        """Compensate when payment fails."""
        data: PaymentFailed = event.data

        # Cancel the order
        await self.message_bus.publish_async(
            CancelOrder(
                order_id=data.order_id,
                reason=f"Payment failed: {data.reason}",
            )
        )

    async def handle_inventory_reserved(self, event: Event) -> None:
        """Complete saga when inventory is reserved."""
        data: InventoryReserved = event.data

        # Confirm the order
        await self.message_bus.publish_async(
            ConfirmOrder(order_id=data.order_id)
        )

    async def handle_inventory_reservation_failed(self, event: Event) -> None:
        """Compensate when inventory reservation fails."""
        data: InventoryReservationFailed = event.data

        # Load order to get payment info
        order = await self.repository.load_async(Order, data.order_id)

        if order.payment_id:
            # Calculate refund amount
            total = sum(item.total_price for item in data.items)

            # Refund payment
            await self.message_bus.publish_async(
                RefundPayment(
                    order_id=data.order_id,
                    payment_id=order.payment_id,
                    amount=total,
                )
            )

        # Cancel order
        await self.message_bus.publish_async(
            CancelOrder(
                order_id=data.order_id,
                reason=f"Inventory reservation failed: {data.reason}",
            )
        )

    async def handle_order_cancelled(self, event: Event) -> None:
        """Clean up when order is cancelled."""
        data: OrderCancelled = event.data

        # Load order to check what needs cleanup
        order = await self.repository.load_async(Order, data.order_id)

        # Release inventory if it was reserved
        if order.reservation_id:
            await self.message_bus.publish_async(
                ReleaseInventory(
                    order_id=data.order_id,
                    reservation_id=order.reservation_id,
                )
            )

        # Note: Payment refund is handled separately in handle_inventory_reservation_failed


def register_saga(
    message_bus: MessageBus, repository: AggregateRepository
) -> OrderSaga:
    """Register saga event handlers with the message bus."""
    saga = OrderSaga(message_bus=message_bus, repository=repository)

    # Subscribe to domain events
    message_bus.subscribe(OrderCreated, saga.handle_order_created)
    message_bus.subscribe(PaymentCompleted, saga.handle_payment_completed)
    message_bus.subscribe(PaymentFailed, saga.handle_payment_failed)
    message_bus.subscribe(InventoryReserved, saga.handle_inventory_reserved)
    message_bus.subscribe(
        InventoryReservationFailed, saga.handle_inventory_reservation_failed
    )
    message_bus.subscribe(OrderCancelled, saga.handle_order_cancelled)

    return saga
