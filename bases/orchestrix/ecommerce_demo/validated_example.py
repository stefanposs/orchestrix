"""Example: Message validation with __post_init__.

Shows how to add native Python validation to Commands and Events
without external dependencies.
"""

from dataclasses import dataclass

from orchestrix.core.common.validation import (
    ValidationError,
    validate_in_range,
    validate_not_empty,
    validate_one_of,
    validate_positive,
)
from orchestrix.core.messaging.message import Command, Event


@dataclass(frozen=True)
class CreateOrder(Command):
    """Create a new order with validation.

    Validates:
    - order_id is not empty
    - customer_name is not empty
    - total_amount is positive
    """

    order_id: str
    customer_name: str
    total_amount: float

    def __post_init__(self) -> None:
        """Validate command fields."""
        validate_not_empty(self.order_id, "order_id")
        validate_not_empty(self.customer_name, "customer_name")
        validate_positive(self.total_amount, "total_amount")


@dataclass(frozen=True)
class UpdateOrderStatus(Command):
    """Update order status with validation.

    Validates:
    - order_id is not empty
    - status is one of allowed values
    """

    order_id: str
    status: str

    def __post_init__(self) -> None:
        """Validate command fields."""
        validate_not_empty(self.order_id, "order_id")
        allowed_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        validate_one_of(self.status, allowed_statuses, "status")


@dataclass(frozen=True)
class RateOrder(Command):
    """Rate an order with validation.

    Validates:
    - order_id is not empty
    - rating is between 1 and 5
    """

    order_id: str
    rating: int

    def __post_init__(self) -> None:
        """Validate command fields."""
        validate_not_empty(self.order_id, "order_id")
        validate_in_range(self.rating, 1, 5, "rating")


@dataclass(frozen=True)
class OrderCreated(Event):
    """Order created event with validation."""

    order_id: str
    customer_name: str
    total_amount: float

    def __post_init__(self) -> None:
        """Validate event fields."""
        validate_not_empty(self.order_id, "order_id")
        validate_not_empty(self.customer_name, "customer_name")
        validate_positive(self.total_amount, "total_amount")


def main() -> None:
    """Demonstrate validation in action."""
    print("=== Valid Commands ===")

    # Valid command - should work
    try:
        order = CreateOrder(
            order_id="ORD-001",
            customer_name="Alice",
            total_amount=99.99,
        )
        print(f"✅ Created order: {order.order_id}")
    except ValidationError as e:
        print(f"❌ Validation failed: {e}")

    # Valid status update
    try:
        status_update = UpdateOrderStatus(
            order_id="ORD-001",
            status="confirmed",
        )
        print(f"✅ Updated status to: {status_update.status}")
    except ValidationError as e:
        print(f"❌ Validation failed: {e}")

    # Valid rating
    try:
        rating = RateOrder(order_id="ORD-001", rating=5)
        print(f"✅ Rated order: {rating.rating} stars")
    except ValidationError as e:
        print(f"❌ Validation failed: {e}")

    print("\n=== Invalid Commands ===")

    # Empty order_id
    try:
        CreateOrder(
            order_id="",
            customer_name="Bob",
            total_amount=50.00,
        )
        print("❌ Should have failed!")
    except ValidationError as e:
        print(f"✅ Caught error: {e}")

    # Negative amount
    try:
        CreateOrder(
            order_id="ORD-002",
            customer_name="Charlie",
            total_amount=-10.00,
        )
        print("❌ Should have failed!")
    except ValidationError as e:
        print(f"✅ Caught error: {e}")

    # Invalid status
    try:
        UpdateOrderStatus(
            order_id="ORD-001",
            status="invalid_status",
        )
        print("❌ Should have failed!")
    except ValidationError as e:
        print(f"✅ Caught error: {e}")

    # Rating out of range
    try:
        RateOrder(order_id="ORD-001", rating=10)
        print("❌ Should have failed!")
    except ValidationError as e:
        print(f"✅ Caught error: {e}")

    print("\n=== Validation protects your domain model! ===")


if __name__ == "__main__":
    main()
