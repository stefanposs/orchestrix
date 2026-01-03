"""Domain models for the e-commerce example."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    """Order lifecycle states."""

    PENDING = "pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    INVENTORY_RESERVED = "inventory_reserved"
    INVENTORY_FAILED = "inventory_failed"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, Enum):
    """Payment processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass(frozen=True)
class OrderItem:
    """Item in an order."""

    product_id: str
    quantity: int
    unit_price: Decimal

    @property
    def total_price(self) -> Decimal:
        """Calculate total price for this item."""
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Address:
    """Shipping or billing address."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str


@dataclass(frozen=True)
class PaymentDetails:
    """Payment information."""

    method: str  # e.g., "credit_card", "paypal"
    transaction_id: str | None = None
    amount: Decimal | None = None


# Events


@dataclass(frozen=True)
class OrderCreated:
    """Order was created."""

    order_id: str
    customer_id: str
    items: list[OrderItem]
    shipping_address: Address
    created_at: datetime


@dataclass(frozen=True)
class PaymentInitiated:
    """Payment processing started."""

    order_id: str
    payment_id: str
    amount: Decimal
    method: str
    initiated_at: datetime


@dataclass(frozen=True)
class PaymentCompleted:
    """Payment was successful."""

    order_id: str
    payment_id: str
    transaction_id: str
    amount: Decimal
    completed_at: datetime


@dataclass(frozen=True)
class PaymentFailed:
    """Payment failed."""

    order_id: str
    payment_id: str
    reason: str
    failed_at: datetime


@dataclass(frozen=True)
class InventoryReserved:
    """Inventory was reserved for the order."""

    order_id: str
    items: list[OrderItem]
    reservation_id: str
    reserved_at: datetime


@dataclass(frozen=True)
class InventoryReservationFailed:
    """Inventory reservation failed."""

    order_id: str
    items: list[OrderItem]
    reason: str
    failed_at: datetime


@dataclass(frozen=True)
class OrderConfirmed:
    """Order was confirmed and is being fulfilled."""

    order_id: str
    confirmed_at: datetime


@dataclass(frozen=True)
class OrderCancelled:
    """Order was cancelled."""

    order_id: str
    reason: str
    cancelled_at: datetime


@dataclass(frozen=True)
class OrderCompleted:
    """Order fulfillment completed."""

    order_id: str
    completed_at: datetime


@dataclass(frozen=True)
class InventoryReleased:
    """Inventory reservation was released (compensation)."""

    order_id: str
    reservation_id: str
    released_at: datetime


@dataclass(frozen=True)
class PaymentRefunded:
    """Payment was refunded (compensation)."""

    order_id: str
    payment_id: str
    refund_id: str
    amount: Decimal
    refunded_at: datetime


# Commands


@dataclass(frozen=True)
class CreateOrder:
    """Create a new order."""

    order_id: str
    customer_id: str
    items: list[OrderItem]
    shipping_address: Address


@dataclass(frozen=True)
class ProcessPayment:
    """Process payment for an order."""

    order_id: str
    payment_id: str
    amount: Decimal
    method: str


@dataclass(frozen=True)
class ReserveInventory:
    """Reserve inventory for an order."""

    order_id: str
    items: list[OrderItem]


@dataclass(frozen=True)
class ConfirmOrder:
    """Confirm an order after payment and inventory reservation."""

    order_id: str


@dataclass(frozen=True)
class CancelOrder:
    """Cancel an order."""

    order_id: str
    reason: str


@dataclass(frozen=True)
class ReleaseInventory:
    """Release inventory reservation (compensation)."""

    order_id: str
    reservation_id: str


@dataclass(frozen=True)
class RefundPayment:
    """Refund a payment (compensation)."""

    order_id: str
    payment_id: str
    amount: Decimal
