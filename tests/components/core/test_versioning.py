"""Tests for event versioning and upcasting."""

from __future__ import annotations

import pytest
from dataclasses import dataclass

from orchestrix.core.message import Event
from orchestrix.core.versioning import (
    EventUpcaster,
    UpcasterRegistry,
    VersionedEvent,
    UpcasterException,
)


# Test event types with multiple versions
@dataclass(frozen=True)
class OrderCreatedV1(Event):
    """Original order creation event."""

    order_id: str
    customer_id: str
    total: float
    version: int = 1


@dataclass(frozen=True)
class OrderCreatedV2(Event):
    """Order creation with currency field."""

    order_id: str
    customer_id: str
    total: float
    currency: str
    version: int = 2


@dataclass(frozen=True)
class OrderCreatedV3(Event):
    """Order creation with metadata."""

    order_id: str
    customer_id: str
    total: float
    currency: str
    created_by: str
    version: int = 3


@dataclass(frozen=True)
class PaymentProcessedV1(Event):
    """Original payment event."""

    payment_id: str
    order_id: str
    amount: float
    version: int = 1


@dataclass(frozen=True)
class PaymentProcessedV2(Event):
    """Payment with payment method."""

    payment_id: str
    order_id: str
    amount: float
    method: str
    version: int = 2


# Test upcasters
class OrderCreatedV1toV2(EventUpcaster[OrderCreatedV1, OrderCreatedV2]):
    """Migrate order creation from v1 to v2."""

    def __init__(self) -> None:
        super().__init__(source_version=1, target_version=2)

    async def upcast(self, event: OrderCreatedV1) -> OrderCreatedV2:
        return OrderCreatedV2(
            order_id=event.order_id,
            customer_id=event.customer_id,
            total=event.total,
            currency="USD",  # Default currency
        )


class OrderCreatedV2toV3(EventUpcaster[OrderCreatedV2, OrderCreatedV3]):
    """Migrate order creation from v2 to v3."""

    def __init__(self) -> None:
        super().__init__(source_version=2, target_version=3)

    async def upcast(self, event: OrderCreatedV2) -> OrderCreatedV3:
        return OrderCreatedV3(
            order_id=event.order_id,
            customer_id=event.customer_id,
            total=event.total,
            currency=event.currency,
            created_by="system",  # Default creator
        )


class PaymentProcessedV1toV2(EventUpcaster[PaymentProcessedV1, PaymentProcessedV2]):
    """Migrate payment from v1 to v2."""

    def __init__(self) -> None:
        super().__init__(source_version=1, target_version=2)

    async def upcast(self, event: PaymentProcessedV1) -> PaymentProcessedV2:
        return PaymentProcessedV2(
            payment_id=event.payment_id,
            order_id=event.order_id,
            amount=event.amount,
            method="credit_card",  # Default method
        )


class TestEventUpcaster:
    """Tests for EventUpcaster base class."""

    def test_upcaster_initialization(self) -> None:
        """Test creating upcaster with version info."""
        upcaster = OrderCreatedV1toV2()
        assert upcaster.source_version == 1
        assert upcaster.target_version == 2

    def test_upcaster_invalid_source_version(self) -> None:
        """Test upcaster rejects invalid source version."""
        with pytest.raises(ValueError, match="source_version"):

            class BadUpcaster(EventUpcaster):
                def __init__(self) -> None:
                    super().__init__(source_version=0, target_version=2)

                async def upcast(self, event):
                    pass

            BadUpcaster()

    def test_upcaster_invalid_target_version(self) -> None:
        """Test upcaster rejects invalid target version."""
        with pytest.raises(ValueError, match="target_version"):

            class BadUpcaster(EventUpcaster):
                def __init__(self) -> None:
                    super().__init__(source_version=1, target_version=-1)

                async def upcast(self, event):
                    pass

            BadUpcaster()

    def test_upcaster_target_not_greater_than_source(self) -> None:
        """Test target version must be greater than source."""
        with pytest.raises(ValueError, match="greater"):

            class BadUpcaster(EventUpcaster):
                def __init__(self) -> None:
                    super().__init__(source_version=2, target_version=2)

                async def upcast(self, event):
                    pass

            BadUpcaster()

    @pytest.mark.asyncio
    async def test_single_upcast(self) -> None:
        """Test single-step event upcasting."""
        upcaster = OrderCreatedV1toV2()
        event_v1 = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )

        event_v2 = await upcaster.upcast(event_v1)

        assert event_v2.order_id == "order-123"
        assert event_v2.customer_id == "cust-456"
        assert event_v2.total == 99.99
        assert event_v2.currency == "USD"


class TestVersionedEvent:
    """Tests for VersionedEvent wrapper."""

    def test_versioned_event_creation(self) -> None:
        """Test creating versioned event."""
        event = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )
        versioned = VersionedEvent(
            event=event, version=1, event_type="OrderCreated"
        )

        assert versioned.event == event
        assert versioned.version == 1
        assert versioned.event_type == "OrderCreated"

    def test_versioned_event_invalid_version(self) -> None:
        """Test versioned event rejects invalid version."""
        event = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )
        with pytest.raises(ValueError, match="version"):
            VersionedEvent(event=event, version=0, event_type="OrderCreated")

    def test_versioned_event_invalid_type(self) -> None:
        """Test versioned event requires event type."""
        event = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )
        with pytest.raises(ValueError, match="event_type"):
            VersionedEvent(event=event, version=1, event_type="")


class TestUpcasterRegistry:
    """Tests for UpcasterRegistry."""

    def test_registry_initialization(self) -> None:
        """Test creating empty registry."""
        registry = UpcasterRegistry()
        assert isinstance(registry, UpcasterRegistry)

    def test_register_upcaster(self) -> None:
        """Test registering single upcaster."""
        registry = UpcasterRegistry()
        upcaster = OrderCreatedV1toV2()

        registry.register("OrderCreated", upcaster)

        assert registry.get_upcaster("OrderCreated", 1, 2) == upcaster

    def test_register_duplicate_upcaster(self) -> None:
        """Test registry prevents duplicate upcasters."""
        registry = UpcasterRegistry()
        upcaster = OrderCreatedV1toV2()

        registry.register("OrderCreated", upcaster)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("OrderCreated", upcaster)

    def test_get_nonexistent_upcaster(self) -> None:
        """Test getting upcaster that isn't registered."""
        registry = UpcasterRegistry()
        result = registry.get_upcaster("OrderCreated", 5, 6)
        assert result is None

    def test_register_invalid_event_type(self) -> None:
        """Test registry rejects invalid event type."""
        registry = UpcasterRegistry()
        upcaster = OrderCreatedV1toV2()

        with pytest.raises(ValueError, match="event_type"):
            registry.register("", upcaster)

    @pytest.mark.asyncio
    async def test_upcast_single_step(self) -> None:
        """Test upcasting single step through registry."""
        registry = UpcasterRegistry()
        registry.register("OrderCreated", OrderCreatedV1toV2())

        event_v1 = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )

        result = await registry.upcast(event_v1, "OrderCreated", target_version=2)

        assert isinstance(result, OrderCreatedV2)
        assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_upcast_multi_step_chain(self) -> None:
        """Test upcasting through multiple steps (v1 -> v2 -> v3)."""
        registry = UpcasterRegistry()
        registry.register("OrderCreated", OrderCreatedV1toV2())
        registry.register("OrderCreated", OrderCreatedV2toV3())

        event_v1 = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )

        result = await registry.upcast(event_v1, "OrderCreated", target_version=3)

        assert isinstance(result, OrderCreatedV3)
        assert result.currency == "USD"
        assert result.created_by == "system"

    @pytest.mark.asyncio
    async def test_upcast_same_version(self) -> None:
        """Test upcasting to same version returns unchanged."""
        registry = UpcasterRegistry()
        event_v2 = OrderCreatedV2(
            order_id="order-123",
            customer_id="cust-456",
            total=99.99,
            currency="EUR",
        )

        result = await registry.upcast(event_v2, "OrderCreated", target_version=2)

        assert result == event_v2

    @pytest.mark.asyncio
    async def test_upcast_missing_chain(self) -> None:
        """Test upcasting fails when chain incomplete."""
        registry = UpcasterRegistry()
        registry.register("OrderCreated", OrderCreatedV1toV2())
        # Missing v2->v3 upcaster

        event_v1 = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )

        with pytest.raises(UpcasterException, match="No upcaster found"):
            await registry.upcast(event_v1, "OrderCreated", target_version=3)

    @pytest.mark.asyncio
    async def test_upcast_no_version_attribute(self) -> None:
        """Test upcasting fails on event without version."""

        @dataclass(frozen=True)
        class BadEvent(Event):
            value: str

        registry = UpcasterRegistry()
        event = BadEvent(value="test")

        with pytest.raises(UpcasterException, match="version attribute"):
            await registry.upcast(event, "BadEvent", target_version=2)

    @pytest.mark.asyncio
    async def test_upcast_downcast_prevented(self) -> None:
        """Test upcasting prevents downcasting to older versions."""
        registry = UpcasterRegistry()

        event_v3 = OrderCreatedV3(
            order_id="order-123",
            customer_id="cust-456",
            total=99.99,
            currency="USD",
            created_by="system",
        )

        with pytest.raises(UpcasterException, match="downcast"):
            await registry.upcast(event_v3, "OrderCreated", target_version=1)

    def test_get_chain_info(self) -> None:
        """Test retrieving available upcasting paths."""
        registry = UpcasterRegistry()
        registry.register("OrderCreated", OrderCreatedV1toV2())
        registry.register("OrderCreated", OrderCreatedV2toV3())
        registry.register("Payment", PaymentProcessedV1toV2())

        order_chain = registry.get_chain_info("OrderCreated")
        assert (1, 2) in order_chain
        assert (2, 3) in order_chain
        assert len(order_chain) == 2

        payment_chain = registry.get_chain_info("Payment")
        assert (1, 2) in payment_chain
        assert len(payment_chain) == 1

        missing_chain = registry.get_chain_info("Unknown")
        assert missing_chain == []

    @pytest.mark.asyncio
    async def test_multiple_event_types(self) -> None:
        """Test registry handling multiple event types."""
        registry = UpcasterRegistry()
        registry.register("OrderCreated", OrderCreatedV1toV2())
        registry.register("PaymentProcessed", PaymentProcessedV1toV2())

        order_v1 = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )
        payment_v1 = PaymentProcessedV1(
            payment_id="pay-789", order_id="order-123", amount=99.99
        )

        order_v2 = await registry.upcast(order_v1, "OrderCreated", target_version=2)
        payment_v2 = await registry.upcast(
            payment_v1, "PaymentProcessed", target_version=2
        )

        assert isinstance(order_v2, OrderCreatedV2)
        assert isinstance(payment_v2, PaymentProcessedV2)
        assert order_v2.currency == "USD"
        assert payment_v2.method == "credit_card"

    @pytest.mark.asyncio
    async def test_upcast_failure_handling(self) -> None:
        """Test registry handles upcast transformation failures."""

        class FailingUpcaster(EventUpcaster):
            def __init__(self) -> None:
                super().__init__(source_version=1, target_version=2)

            async def upcast(self, event):
                raise RuntimeError("Transformation failed")

        registry = UpcasterRegistry()
        registry.register("BadEvent", FailingUpcaster())

        @dataclass(frozen=True)
        class BadEventV1(Event):
            value: str
            version: int = 1

        event = BadEventV1(value="test")

        with pytest.raises(UpcasterException, match="failed"):
            await registry.upcast(event, "BadEvent", target_version=2)

    @pytest.mark.asyncio
    async def test_intermediate_version_upcasting(self) -> None:
        """Test upcasting to intermediate version in chain."""
        registry = UpcasterRegistry()
        registry.register("OrderCreated", OrderCreatedV1toV2())
        registry.register("OrderCreated", OrderCreatedV2toV3())

        event_v1 = OrderCreatedV1(
            order_id="order-123", customer_id="cust-456", total=99.99
        )

        # Upcast only to v2, not all the way to v3
        result = await registry.upcast(event_v1, "OrderCreated", target_version=2)

        assert isinstance(result, OrderCreatedV2)
        assert result.currency == "USD"
        # Version 3 fields should not be present
        assert not hasattr(result, "created_by")
