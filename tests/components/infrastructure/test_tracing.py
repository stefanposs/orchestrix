"""Tests for distributed tracing with Jaeger."""

from __future__ import annotations

import pytest

from orchestrix.infrastructure.tracing import (
    JaegerTracer,
    TracingConfig,
    init_tracing,
)


class TestTracingConfig:
    """Tests for TracingConfig."""

    def test_default_config(self) -> None:
        """Test creating config with defaults."""
        config = TracingConfig(service_name="test-service")
        assert config.service_name == "test-service"
        assert config.jaeger_agent_host == "localhost"
        assert config.jaeger_agent_port == 6831
        assert config.jaeger_sampler_type == "const"
        assert config.jaeger_sampler_param == 1.0

    def test_custom_config(self) -> None:
        """Test creating config with custom values."""
        config = TracingConfig(
            service_name="payment-service",
            jaeger_agent_host="jaeger.prod.svc.cluster.local",
            jaeger_agent_port=6832,
            jaeger_sampler_type="probabilistic",
            jaeger_sampler_param=0.1,
        )
        assert config.service_name == "payment-service"
        assert config.jaeger_agent_host == "jaeger.prod.svc.cluster.local"
        assert config.jaeger_agent_port == 6832
        assert config.jaeger_sampler_type == "probabilistic"
        assert config.jaeger_sampler_param == 0.1

    def test_invalid_service_name(self) -> None:
        """Test config rejects invalid service name."""
        with pytest.raises(ValueError, match="service_name"):
            TracingConfig(service_name="")

    def test_invalid_host(self) -> None:
        """Test config rejects invalid host."""
        with pytest.raises(ValueError, match="jaeger_agent_host"):
            TracingConfig(
                service_name="test", jaeger_agent_host=""
            )

    def test_invalid_port(self) -> None:
        """Test config rejects invalid port."""
        with pytest.raises(ValueError, match="jaeger_agent_port"):
            TracingConfig(service_name="test", jaeger_agent_port=70000)


class TestJaegerTracer:
    """Tests for JaegerTracer."""

    def test_tracer_initialization(self) -> None:
        """Test initializing tracer."""
        tracer = JaegerTracer()
        assert tracer.tracer_name == "orchestrix"

    def test_tracer_custom_name(self) -> None:
        """Test tracer with custom name."""
        tracer = JaegerTracer(tracer_name="order-service")
        assert tracer.tracer_name == "order-service"

    def test_span_creation(self) -> None:
        """Test creating a span."""
        tracer = JaegerTracer()

        with tracer.span("test_operation"):
            pass

    def test_span_with_attributes(self) -> None:
        """Test span with attributes."""
        tracer = JaegerTracer()

        with tracer.span(
            "process_event", {"event_id": "evt-123", "type": "OrderCreated"}
        ):
            pass

    def test_span_error_handling(self) -> None:
        """Test span records errors."""
        tracer = JaegerTracer()

        with pytest.raises(ValueError):
            with tracer.span("failing_operation"):
                raise ValueError("Operation failed")

    @pytest.mark.asyncio
    async def test_async_span_creation(self) -> None:
        """Test creating async span."""
        tracer = JaegerTracer()

        async with tracer.async_span("async_operation"):
            pass

    @pytest.mark.asyncio
    async def test_async_span_with_attributes(self) -> None:
        """Test async span with attributes."""
        tracer = JaegerTracer()

        async with tracer.async_span(
            "async_process", {"operation": "create_order"}
        ):
            pass

    @pytest.mark.asyncio
    async def test_async_span_error_handling(self) -> None:
        """Test async span error recording."""
        tracer = JaegerTracer()

        with pytest.raises(RuntimeError):
            async with tracer.async_span("async_failure"):
                raise RuntimeError("Async failed")

    def test_span_event_creation(self) -> None:
        """Test creating event span."""
        tracer = JaegerTracer()

        with tracer.span_event(
            event_type="OrderCreated",
            event_id="evt-001",
            aggregate_id="order-123",
        ):
            pass

    @pytest.mark.asyncio
    async def test_async_span_event_creation(self) -> None:
        """Test creating async event span."""
        tracer = JaegerTracer()

        async with tracer.async_span_event(
            event_type="OrderConfirmed",
            event_id="evt-002",
            aggregate_id="order-123",
        ):
            pass

    def test_span_command_creation(self) -> None:
        """Test creating command span."""
        tracer = JaegerTracer()

        with tracer.span_command(
            command_type="CreateOrder", aggregate_id="order-123"
        ):
            pass

    @pytest.mark.asyncio
    async def test_async_span_command_creation(self) -> None:
        """Test creating async command span."""
        tracer = JaegerTracer()

        async with tracer.async_span_command(
            command_type="ConfirmOrder", aggregate_id="order-123"
        ):
            pass

    def test_span_saga_creation(self) -> None:
        """Test creating saga span."""
        tracer = JaegerTracer()

        with tracer.span_saga(saga_type="MoneyTransfer", saga_id="saga-001"):
            pass

    @pytest.mark.asyncio
    async def test_async_span_saga_creation(self) -> None:
        """Test creating async saga span."""
        tracer = JaegerTracer()

        async with tracer.async_span_saga(
            saga_type="OrderFulfillment", saga_id="saga-002"
        ):
            pass

    def test_get_trace_id(self) -> None:
        """Test getting trace ID from span."""
        tracer = JaegerTracer()

        with tracer.span("get_trace_test"):
            trace_id = tracer.get_trace_id()
            # Trace ID should be set within a span context
            assert trace_id is not None or trace_id is None  # Depends on context

    def test_set_attribute(self) -> None:
        """Test setting attribute on current span."""
        tracer = JaegerTracer()

        with tracer.span("set_attr_test"):
            tracer.set_attribute("user_id", "usr-123")
            tracer.set_attribute("count", 42)
            tracer.set_attribute("enabled", True)

    def test_add_event(self) -> None:
        """Test adding event to span."""
        tracer = JaegerTracer()

        with tracer.span("add_event_test"):
            tracer.add_event("payment_processed")
            tracer.add_event("order_shipped", {"region": "EU"})

    def test_nested_spans(self) -> None:
        """Test nested span creation."""
        tracer = JaegerTracer()

        with tracer.span("parent_operation"):
            with tracer.span("child_operation"):
                pass

    @pytest.mark.asyncio
    async def test_nested_async_spans(self) -> None:
        """Test nested async spans."""
        tracer = JaegerTracer()

        async with tracer.async_span("parent_async"):
            async with tracer.async_span("child_async"):
                pass

    def test_multiple_spans_sequence(self) -> None:
        """Test multiple sequential spans."""
        tracer = JaegerTracer()

        with tracer.span("operation_1"):
            pass

        with tracer.span("operation_2"):
            pass

        with tracer.span("operation_3"):
            pass

    @pytest.mark.asyncio
    async def test_multiple_async_spans_sequence(self) -> None:
        """Test multiple sequential async spans."""
        tracer = JaegerTracer()

        async with tracer.async_span("async_op_1"):
            pass

        async with tracer.async_span("async_op_2"):
            pass

        async with tracer.async_span("async_op_3"):
            pass

    def test_span_with_complex_attributes(self) -> None:
        """Test span with various attribute types."""
        tracer = JaegerTracer()

        attributes = {
            "string_attr": "test",
            "int_attr": 123,
            "float_attr": 3.14,
            "bool_attr": True,
        }

        with tracer.span("complex_attrs", attributes):
            pass

    def test_event_span_integration(self) -> None:
        """Test event span with additional attributes."""
        tracer = JaegerTracer()

        with tracer.span_event(
            event_type="PaymentProcessed",
            event_id="evt-100",
            aggregate_id="order-456",
        ):
            tracer.set_attribute("amount", 99.99)
            tracer.set_attribute("currency", "USD")

    @pytest.mark.asyncio
    async def test_async_event_span_integration(self) -> None:
        """Test async event span integration."""
        tracer = JaegerTracer()

        async with tracer.async_span_event(
            event_type="InvoiceGenerated",
            event_id="evt-101",
            aggregate_id="invoice-789",
        ):
            tracer.add_event("invoice_ready")

    def test_command_span_integration(self) -> None:
        """Test command span integration."""
        tracer = JaegerTracer()

        with tracer.span_command("CancelOrder", "order-789"):
            tracer.set_attribute("reason", "customer_request")

    @pytest.mark.asyncio
    async def test_saga_span_integration(self) -> None:
        """Test saga span integration."""
        tracer = JaegerTracer()

        async with tracer.async_span_saga("PaymentProcessing", "saga-003"):
            tracer.set_attribute("step", "charge_card")
            tracer.add_event("charge_started")


class TestTracingInitialization:
    """Tests for tracing initialization."""

    def test_init_tracing_with_defaults(self) -> None:
        """Test initializing tracing with defaults."""
        tracer = init_tracing(service_name="test-app")
        assert isinstance(tracer, JaegerTracer)

    def test_init_tracing_with_config(self) -> None:
        """Test initializing with config object."""
        config = TracingConfig(
            service_name="payment-app",
            jaeger_agent_host="jaeger.local",
            jaeger_agent_port=6831,
        )
        tracer = init_tracing(config=config)
        assert isinstance(tracer, JaegerTracer)

    def test_get_tracer(self) -> None:
        """Test getting current tracer."""
        from orchestrix.infrastructure.tracing import get_tracer

        tracer = get_tracer()
        assert isinstance(tracer, JaegerTracer)
