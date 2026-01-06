"""Tests for message validation in integration."""

from dataclasses import dataclass

import pytest
from orchestrix.core.common.validation import (
    ValidationError,
    validate_not_empty,
    validate_positive,
)
from orchestrix.core.messaging.message import Command
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus


@dataclass(frozen=True)
class CreateValidatedOrder(Command):
    """Command with validation."""

    order_id: str = "ORD-001"
    total_amount: float = 100.0

    def __post_init__(self) -> None:
        """Validate fields."""
        # Call parent __post_init__ first (for Message fields)
        super().__post_init__()
        # Then validate our fields
        validate_not_empty(self.order_id, "order_id")
        validate_positive(self.total_amount, "total_amount")


class TestValidationIntegration:
    """Test validation in message bus context."""

    def test_valid_command_is_published(self) -> None:
        """Valid command should be published successfully."""
        bus = InMemoryMessageBus()
        handler_called = []

        def handler(msg: CreateValidatedOrder) -> None:
            handler_called.append(msg)

        bus.subscribe(CreateValidatedOrder, handler)

        # Valid command
        cmd = CreateValidatedOrder(order_id="ORD-123", total_amount=99.99)
        bus.publish(cmd)

        assert len(handler_called) == 1
        assert handler_called[0].order_id == "ORD-123"

    def test_invalid_command_raises_on_creation(self) -> None:
        """Invalid command should raise ValidationError on creation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateValidatedOrder(order_id="", total_amount=50.0)

        assert "order_id cannot be empty" in str(exc_info.value)

    def test_cannot_publish_invalid_command(self) -> None:
        """Cannot even create an invalid command to publish."""
        # Try to create invalid command - should raise before publish
        with pytest.raises(ValidationError):
            CreateValidatedOrder(order_id="ORD-001", total_amount=-10.0)

    def test_validation_error_has_field_info(self) -> None:
        """ValidationError should include field information."""
        with pytest.raises(ValidationError) as exc_info:
            CreateValidatedOrder(order_id="", total_amount=50.0)

        error = exc_info.value
        assert error.field == "order_id"
        assert error.value == ""
        assert "order_id" in str(error)

    def test_multiple_handlers_receive_valid_command(self) -> None:
        """Multiple handlers should all receive validated command."""
        bus = InMemoryMessageBus()
        calls = []

        def handler1(msg: CreateValidatedOrder) -> None:
            calls.append(("h1", msg.order_id))

        def handler2(msg: CreateValidatedOrder) -> None:
            calls.append(("h2", msg.order_id))

        bus.subscribe(CreateValidatedOrder, handler1)
        bus.subscribe(CreateValidatedOrder, handler2)

        cmd = CreateValidatedOrder(order_id="ORD-456", total_amount=199.99)
        bus.publish(cmd)

        assert len(calls) == 2
        assert ("h1", "ORD-456") in calls
        assert ("h2", "ORD-456") in calls

    def test_validation_prevents_bad_data_in_system(self) -> None:
        """Validation ensures only valid data enters the system."""
        bus = InMemoryMessageBus()
        processed_orders = []

        def process_order(msg: CreateValidatedOrder) -> None:
            # Handler can trust that data is valid
            assert msg.order_id  # Never empty
            assert msg.total_amount > 0  # Always positive
            processed_orders.append(msg.order_id)

        bus.subscribe(CreateValidatedOrder, process_order)

        # Valid commands work
        bus.publish(CreateValidatedOrder(order_id="ORD-001", total_amount=50.0))
        bus.publish(CreateValidatedOrder(order_id="ORD-002", total_amount=75.0))

        assert processed_orders == ["ORD-001", "ORD-002"]

        # Invalid commands cannot even be created
        with pytest.raises(ValidationError):
            CreateValidatedOrder(order_id="ORD-003", total_amount=0)
