"""Order aggregate implementation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from orchestrix.core.aggregate import AggregateRoot

from .models import (
    Address,
    InventoryReleased,
    InventoryReservationFailed,
    InventoryReserved,
    OrderCancelled,
    OrderCompleted,
    OrderConfirmed,
    OrderCreated,
    OrderItem,
    OrderStatus,
    PaymentCompleted,
    PaymentFailed,
    PaymentInitiated,
    PaymentRefunded,
)


@dataclass
class Order(AggregateRoot):
    """Order aggregate managing the order lifecycle."""

    customer_id: str = ""
    items: list[OrderItem] = field(default_factory=list)
    shipping_address: Address | None = None
    status: OrderStatus = OrderStatus.PENDING
    payment_id: str | None = None
    reservation_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def create(
        self,
        order_id: str,
        customer_id: str,
        items: list[OrderItem],
        shipping_address: Address,
    ) -> None:
        """Create a new order."""
        if self.customer_id:
            msg = "Order already created"
            raise ValueError(msg)

        if not items:
            msg = "Order must have at least one item"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            OrderCreated(
                order_id=order_id,
                customer_id=customer_id,
                items=items,
                shipping_address=shipping_address,
                created_at=now,
            )
        )

    def initiate_payment(self, payment_id: str, amount: float, method: str) -> None:
        """Start payment processing."""
        if self.status != OrderStatus.PENDING:
            msg = f"Cannot initiate payment for order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            PaymentInitiated(
                order_id=self.aggregate_id,
                payment_id=payment_id,
                amount=amount,
                method=method,
                initiated_at=now,
            )
        )

    def complete_payment(self, payment_id: str, transaction_id: str, amount: float) -> None:
        """Mark payment as completed."""
        if self.status != OrderStatus.PAYMENT_PROCESSING:
            msg = f"Cannot complete payment for order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            PaymentCompleted(
                order_id=self.aggregate_id,
                payment_id=payment_id,
                transaction_id=transaction_id,
                amount=amount,
                completed_at=now,
            )
        )

    def fail_payment(self, payment_id: str, reason: str) -> None:
        """Mark payment as failed."""
        if self.status != OrderStatus.PAYMENT_PROCESSING:
            msg = f"Cannot fail payment for order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            PaymentFailed(
                order_id=self.aggregate_id,
                payment_id=payment_id,
                reason=reason,
                failed_at=now,
            )
        )

    def reserve_inventory(self, items: list[OrderItem], reservation_id: str) -> None:
        """Mark inventory as reserved."""
        if self.status != OrderStatus.PAYMENT_COMPLETED:
            msg = f"Cannot reserve inventory for order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            InventoryReserved(
                order_id=self.aggregate_id,
                items=items,
                reservation_id=reservation_id,
                reserved_at=now,
            )
        )

    def fail_inventory_reservation(self, items: list[OrderItem], reason: str) -> None:
        """Mark inventory reservation as failed."""
        if self.status != OrderStatus.PAYMENT_COMPLETED:
            msg = f"Cannot fail inventory reservation for order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            InventoryReservationFailed(
                order_id=self.aggregate_id,
                items=items,
                reason=reason,
                failed_at=now,
            )
        )

    def confirm(self) -> None:
        """Confirm the order after payment and inventory reservation."""
        if self.status != OrderStatus.INVENTORY_RESERVED:
            msg = f"Cannot confirm order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            OrderConfirmed(order_id=self.aggregate_id, confirmed_at=now)
        )

    def cancel(self, reason: str) -> None:
        """Cancel the order."""
        if self.status in (
            OrderStatus.CONFIRMED,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        ):
            msg = f"Cannot cancel order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            OrderCancelled(order_id=self.aggregate_id, reason=reason, cancelled_at=now)
        )

    def complete(self) -> None:
        """Mark order as completed."""
        if self.status != OrderStatus.CONFIRMED:
            msg = f"Cannot complete order in {self.status} status"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            OrderCompleted(order_id=self.aggregate_id, completed_at=now)
        )

    def release_inventory(self, reservation_id: str) -> None:
        """Release inventory reservation (compensation)."""
        now = datetime.now(timezone.utc)
        self._apply_event(
            InventoryReleased(
                order_id=self.aggregate_id,
                reservation_id=reservation_id,
                released_at=now,
            )
        )

    def refund_payment(self, payment_id: str, refund_id: str, amount: float) -> None:
        """Refund payment (compensation)."""
        now = datetime.now(timezone.utc)
        self._apply_event(
            PaymentRefunded(
                order_id=self.aggregate_id,
                payment_id=payment_id,
                refund_id=refund_id,
                amount=amount,
                refunded_at=now,
            )
        )

    # Event handlers

    def _when_order_created(self, event: OrderCreated) -> None:
        """Apply OrderCreated event."""
        self.aggregate_id = event.order_id
        self.customer_id = event.customer_id
        self.items = event.items
        self.shipping_address = event.shipping_address
        self.status = OrderStatus.PENDING
        self.created_at = event.created_at
        self.updated_at = event.created_at

    def _when_payment_initiated(self, event: PaymentInitiated) -> None:
        """Apply PaymentInitiated event."""
        self.payment_id = event.payment_id
        self.status = OrderStatus.PAYMENT_PROCESSING
        self.updated_at = event.initiated_at

    def _when_payment_completed(self, event: PaymentCompleted) -> None:
        """Apply PaymentCompleted event."""
        self.status = OrderStatus.PAYMENT_COMPLETED
        self.updated_at = event.completed_at

    def _when_payment_failed(self, event: PaymentFailed) -> None:
        """Apply PaymentFailed event."""
        self.status = OrderStatus.PAYMENT_FAILED
        self.updated_at = event.failed_at

    def _when_inventory_reserved(self, event: InventoryReserved) -> None:
        """Apply InventoryReserved event."""
        self.reservation_id = event.reservation_id
        self.status = OrderStatus.INVENTORY_RESERVED
        self.updated_at = event.reserved_at

    def _when_inventory_reservation_failed(self, event: InventoryReservationFailed) -> None:
        """Apply InventoryReservationFailed event."""
        self.status = OrderStatus.INVENTORY_FAILED
        self.updated_at = event.failed_at

    def _when_order_confirmed(self, event: OrderConfirmed) -> None:
        """Apply OrderConfirmed event."""
        self.status = OrderStatus.CONFIRMED
        self.updated_at = event.confirmed_at

    def _when_order_cancelled(self, event: OrderCancelled) -> None:
        """Apply OrderCancelled event."""
        self.status = OrderStatus.CANCELLED
        self.updated_at = event.cancelled_at

    def _when_order_completed(self, event: OrderCompleted) -> None:
        """Apply OrderCompleted event."""
        self.status = OrderStatus.COMPLETED
        self.updated_at = event.completed_at

    def _when_inventory_released(self, event: InventoryReleased) -> None:
        """Apply InventoryReleased event (compensation)."""
        self.reservation_id = None
        self.updated_at = event.released_at

    def _when_payment_refunded(self, event: PaymentRefunded) -> None:
        """Apply PaymentRefunded event (compensation)."""
        self.updated_at = event.refunded_at
