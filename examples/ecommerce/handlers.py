"""Command handlers for order processing."""
from dataclasses import dataclass
from uuid import uuid4

from orchestrix.core.aggregate import AggregateRepository
from orchestrix.core.messaging import MessageBus

from .aggregate import Order
from .models import (
    CancelOrder,
    ConfirmOrder,
    CreateOrder,
    ProcessPayment,
    RefundPayment,
    ReleaseInventory,
    ReserveInventory,
)


@dataclass
class OrderCommandHandlers:
    """Handlers for order-related commands."""

    repository: AggregateRepository
    message_bus: MessageBus

    async def handle_create_order(self, command: CreateOrder) -> None:
        """Create a new order."""
        order = Order()
        order.create(
            order_id=command.order_id,
            customer_id=command.customer_id,
            items=command.items,
            shipping_address=command.shipping_address,
        )

        await self.repository.save_async(order)

        # Publish events to trigger saga
        for event in order.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_process_payment(self, command: ProcessPayment) -> None:
        """Process payment for an order."""
        # Load order
        order = await self.repository.load_async(Order, command.order_id)

        # Initiate payment
        order.initiate_payment(
            payment_id=command.payment_id,
            amount=command.amount,
            method=command.method,
        )

        # Simulate payment processing (in real system, call payment gateway)
        # For demo purposes, payments always succeed
        order.complete_payment(
            payment_id=command.payment_id,
            transaction_id=str(uuid4()),
            amount=command.amount,
        )

        await self.repository.save_async(order)

        # Publish events
        for event in order.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_reserve_inventory(self, command: ReserveInventory) -> None:
        """Reserve inventory for an order."""
        # Load order
        order = await self.repository.load_async(Order, command.order_id)

        # Simulate inventory check (in real system, call inventory service)
        # For demo purposes, always succeed
        reservation_id = str(uuid4())
        order.reserve_inventory(items=command.items, reservation_id=reservation_id)

        await self.repository.save_async(order)

        # Publish events
        for event in order.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_confirm_order(self, command: ConfirmOrder) -> None:
        """Confirm an order."""
        # Load order
        order = await self.repository.load_async(Order, command.order_id)

        order.confirm()

        await self.repository.save_async(order)

        # Publish events
        for event in order.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_cancel_order(self, command: CancelOrder) -> None:
        """Cancel an order."""
        # Load order
        order = await self.repository.load_async(Order, command.order_id)

        order.cancel(reason=command.reason)

        await self.repository.save_async(order)

        # Publish events
        for event in order.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_release_inventory(self, command: ReleaseInventory) -> None:
        """Release inventory reservation (compensation)."""
        # Load order
        order = await self.repository.load_async(Order, command.order_id)

        # Simulate inventory release (in real system, call inventory service)
        order.release_inventory(reservation_id=command.reservation_id)

        await self.repository.save_async(order)

        # Publish events
        for event in order.uncommitted_events:
            await self.message_bus.publish_async(event.data)

    async def handle_refund_payment(self, command: RefundPayment) -> None:
        """Refund a payment (compensation)."""
        # Load order
        order = await self.repository.load_async(Order, command.order_id)

        # Simulate payment refund (in real system, call payment gateway)
        refund_id = str(uuid4())
        order.refund_payment(
            payment_id=command.payment_id,
            refund_id=refund_id,
            amount=command.amount,
        )

        await self.repository.save_async(order)

        # Publish events
        for event in order.uncommitted_events:
            await self.message_bus.publish_async(event.data)


def register_handlers(
    message_bus: MessageBus, repository: AggregateRepository
) -> OrderCommandHandlers:
    """Register command handlers with the message bus."""
    handlers = OrderCommandHandlers(repository=repository, message_bus=message_bus)

    # Subscribe to commands
    message_bus.subscribe(CreateOrder, handlers.handle_create_order)
    message_bus.subscribe(ProcessPayment, handlers.handle_process_payment)
    message_bus.subscribe(ReserveInventory, handlers.handle_reserve_inventory)
    message_bus.subscribe(ConfirmOrder, handlers.handle_confirm_order)
    message_bus.subscribe(CancelOrder, handlers.handle_cancel_order)
    message_bus.subscribe(ReleaseInventory, handlers.handle_release_inventory)
    message_bus.subscribe(RefundPayment, handlers.handle_refund_payment)

    return handlers
