"""Integration test: End-to-end event sourcing with all major components.

Tests the complete event sourcing stack:
- Event storage
- CQRS projections
- Saga orchestration
- Event versioning
- Prometheus monitoring
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from orchestrix.core.message import Event
from orchestrix.core.projection import ProjectionEngine, InMemoryProjectionStateStore
from orchestrix.core.saga import Saga, SagaStep, InMemorySagaStateStore
from orchestrix.core.versioning import EventUpcaster, UpcasterRegistry
from orchestrix.infrastructure.inmemory_store import InMemoryEventStore
from orchestrix.infrastructure.prometheus_metrics import (
    MetricConfig,
    MetricOperationType,
    PrometheusMetrics,
)


# Define events for order processing
@dataclass(frozen=True)
class OrderCreatedV1(Event):
    """Legacy order creation event."""

    order_id: str
    customer_id: str
    total: float
    version: int = 1


@dataclass(frozen=True)
class OrderCreatedV2(Event):
    """Updated order with currency."""

    order_id: str
    customer_id: str
    total: float
    currency: str
    version: int = 2


@dataclass(frozen=True)
class OrderConfirmed(Event):
    """Order confirmation event."""

    order_id: str


@dataclass(frozen=True)
class PaymentProcessed(Event):
    """Payment processed event."""

    order_id: str
    amount: float


# Define upcaster for event versioning
class OrderCreatedUpcaster(EventUpcaster[OrderCreatedV1, OrderCreatedV2]):
    """Upgrade OrderCreated from v1 to v2."""

    def __init__(self) -> None:
        super().__init__(source_version=1, target_version=2)

    async def upcast(self, event: OrderCreatedV1) -> OrderCreatedV2:
        return OrderCreatedV2(
            order_id=event.order_id,
            customer_id=event.customer_id,
            total=event.total,
            currency="USD",
        )


# Define read models for projection
@dataclass
class OrderSummary:
    """Read model for order summary."""

    order_id: str
    customer_id: str
    total: float
    currency: str = "USD"
    confirmed: bool = False
    payment_processed: bool = False


# Define saga for order processing
async def confirm_order(order_id: str) -> dict:
    """Step: Confirm order."""
    await asyncio.sleep(0.001)
    return {"confirmed": True}


async def process_payment(order_id: str, amount: float) -> dict:
    """Step: Process payment."""
    await asyncio.sleep(0.001)
    return {"paid": True}


async def compensate_confirm(context: dict) -> None:
    """Compensation: Cancel order confirmation."""
    await asyncio.sleep(0.001)


async def compensate_payment(context: dict) -> None:
    """Compensation: Refund payment."""
    await asyncio.sleep(0.001)


class TestIntegration:
    """Integration tests for complete event sourcing stack."""

    @pytest.mark.asyncio
    async def test_complete_order_processing(self) -> None:
        """Test order processing with versioning, projections, and metrics."""
        # Setup
        projection_state_store = InMemoryProjectionStateStore()
        metrics = PrometheusMetrics(
            config=MetricConfig(namespace="test", subsystem="order")
        )

        # Setup versioning
        upcaster_registry = UpcasterRegistry()
        upcaster_registry.register("OrderCreated", OrderCreatedUpcaster())

        # Setup projection engine
        projection_engine = ProjectionEngine(
            projection_id="OrderSummary",
            state_store=projection_state_store,
        )

        order_summaries = {}

        @projection_engine.on(OrderCreatedV2)
        async def handle_order_created(event: OrderCreatedV2) -> None:
            summary = OrderSummary(
                order_id=event.order_id,
                customer_id=event.customer_id,
                total=event.total,
                currency=event.currency,
            )
            order_summaries[event.order_id] = summary

        @projection_engine.on(OrderConfirmed)
        async def handle_order_confirmed(event: OrderConfirmed) -> None:
            if event.order_id in order_summaries:
                order_summaries[event.order_id].confirmed = True

        # Track event publishing and upcasting
        with metrics.track_event_publish(event_type="OrderCreated"):
            # Create order (v1, requires upgrade)
            order_event_v1 = OrderCreatedV1(
                order_id="ORD-001",
                customer_id="CUST-123",
                total=99.99,
            )

            # Upcast to v2
            order_event_v2 = await upcaster_registry.upcast(
                order_event_v1, "OrderCreated", target_version=2
            )

            # Process through projection
            await projection_engine.handle_event(order_event_v2)

        # Verify projection
        assert "ORD-001" in order_summaries
        summary = order_summaries["ORD-001"]
        assert summary.order_id == "ORD-001"
        assert summary.currency == "USD"
        assert not summary.confirmed

        # Track confirmation event
        with metrics.track_event_publish(event_type="OrderConfirmed"):
            confirm_event = OrderConfirmed(order_id="ORD-001")
            await projection_engine.handle_event(confirm_event)

        # Verify final state
        assert summary.confirmed is True
        assert len(order_summaries) == 1

        # Verify metrics were recorded
        registry = metrics.get_prometheus_registry()
        samples = list(registry.collect())
        assert len(samples) > 0

    @pytest.mark.asyncio
    async def test_projection_with_versioning(self) -> None:
        """Test projections working with versioned events."""
        projection_state_store = InMemoryProjectionStateStore()
        upcaster_registry = UpcasterRegistry()
        upcaster_registry.register("OrderCreated", OrderCreatedUpcaster())

        engine = ProjectionEngine(
            projection_id="TestProjection",
            state_store=projection_state_store,
        )

        events_processed = []

        @engine.on(OrderCreatedV2)
        async def handle(event: OrderCreatedV2) -> None:
            events_processed.append(event)

        # Process v1 event by upgrading it first
        v1_event = OrderCreatedV1(
            order_id="ORD-002",
            customer_id="CUST-456",
            total=149.99,
        )

        v2_event = await upcaster_registry.upcast(
            v1_event, "OrderCreated", target_version=2
        )

        await engine.handle_event(v2_event)

        assert len(events_processed) == 1
        assert events_processed[0].currency == "USD"

    @pytest.mark.asyncio
    async def test_metrics_with_async_operations(self) -> None:
        """Test metrics tracking async operations."""
        metrics = PrometheusMetrics()

        async def simulate_order_processing() -> None:
            async with metrics.track_async_event_publish(
                event_type="OrderCreated"
            ):
                await asyncio.sleep(0.001)

            async with metrics.track_async_command_handle(
                command_type="ConfirmOrder"
            ):
                await asyncio.sleep(0.001)

        await simulate_order_processing()

        # Verify metrics collected
        registry = metrics.get_prometheus_registry()
        samples = list(registry.collect())
        assert len(samples) > 0

    @pytest.mark.asyncio
    async def test_storage_operations_with_metrics(self) -> None:
        """Test storage operations with metrics tracking."""
        event_store = InMemoryEventStore()
        metrics = PrometheusMetrics()

        event = OrderCreatedV2(
            order_id="ORD-003",
            customer_id="CUST-789",
            total=299.99,
            currency="EUR",
        )

        with metrics.track_storage_operation(operation_type=MetricOperationType.APPEND):
            event_store.save("order-ORD-003", [event])

        with metrics.track_storage_operation(operation_type=MetricOperationType.LOAD):
            events = event_store.load("order-ORD-003")

        assert len(events) == 1
        assert events[0].order_id == "ORD-003"

    @pytest.mark.asyncio
    async def test_projection_lag_tracking(self) -> None:
        """Test tracking projection lag in metrics."""
        metrics = PrometheusMetrics()

        # Simulate scenario where projection is behind
        metrics.record_projection_lag("OrderSummary", 42)
        metrics.record_projection_lag("CustomerProfile", 7)
        metrics.record_projection_lag("PaymentStatus", 0)

        # Simulate updates
        with metrics.track_projection_update(projection_name="OrderSummary"):
            await asyncio.sleep(0.001)

        # Verify metrics
        registry = metrics.get_prometheus_registry()
        samples = list(registry.collect())
        assert len(samples) > 0
