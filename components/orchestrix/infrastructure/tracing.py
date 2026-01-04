"""Distributed tracing with Jaeger and OpenTelemetry integration.

This module provides production-grade distributed tracing for event sourcing systems
using OpenTelemetry and Jaeger as the backend. Track events, commands, and sagas
across microservice boundaries with automatic context propagation.

Key features:
- Automatic span creation for events and commands
- Trace ID propagation across async boundaries
- OpenTelemetry instrumentation
- Jaeger backend integration
- Error and exception tracking
- Performance metrics in traces

Example:
    from orchestrix.infrastructure.tracing import JaegerTracer, init_tracing

    # Initialize tracing
    init_tracing(
        service_name="order-service",
        jaeger_agent_host="localhost",
        jaeger_agent_port=6831
    )

    tracer = JaegerTracer()

    # Automatic tracing
    with tracer.span("process_order", {"order_id": "ORD-001"}):
        # Your code here - automatically traced
        pass

    # Async tracing
    async with tracer.async_span("confirm_order"):
        await confirm_order()
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Generator, Optional

def _check_jaeger_available() -> bool:
    """Check if Jaeger/OpenTelemetry is available."""
    try:
        import opentelemetry.trace  # noqa: F401
        import opentelemetry.sdk.trace  # noqa: F401
        # Try modern OTLP first, fallback to legacy Jaeger
        try:
            import opentelemetry.exporter.otlp.proto.grpc.trace_exporter  # noqa: F401
        except ImportError:
            pass  # OTLP not available, will try Jaeger later
        return True
    except ImportError:
        return False


HAS_JAEGER = _check_jaeger_available()


@dataclass(frozen=True)
class TracingConfig:
    """Configuration for distributed tracing.

    Attributes:
        service_name: Name of the service for tracing
        jaeger_agent_host: Jaeger agent hostname
        jaeger_agent_port: Jaeger agent port (default: 6831)
        jaeger_sampler_type: Sampler type (const, probabilistic, rate_limiting)
        jaeger_sampler_param: Sampler parameter (probability or rate)
    """

    service_name: str
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    jaeger_sampler_type: str = "const"
    jaeger_sampler_param: float = 1.0

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.service_name or not isinstance(self.service_name, str):
            raise ValueError("service_name must be non-empty string")
        if not self.jaeger_agent_host or not isinstance(
            self.jaeger_agent_host, str
        ):
            raise ValueError("jaeger_agent_host must be non-empty string")
        if self.jaeger_agent_port < 1 or self.jaeger_agent_port > 65535:
            raise ValueError("jaeger_agent_port must be between 1 and 65535")


class JaegerTracer:
    """Distributed tracer using Jaeger and OpenTelemetry.

    Provides spans for tracing events, commands, sagas, and other operations
    across microservice boundaries with automatic context propagation.

    Requires opentelemetry-api and opentelemetry-exporter-jaeger:
        pip install opentelemetry-api opentelemetry-exporter-jaeger
    """

    def __init__(self, tracer_name: str = "orchestrix") -> None:
        """Initialize Jaeger tracer.

        Args:
            tracer_name: Name for tracer identification

        Raises:
            ImportError: If Jaeger dependencies not installed
        """
        if not HAS_JAEGER:
            raise ImportError(
                "Jaeger not installed. Install with: "
                "pip install opentelemetry-api opentelemetry-exporter-jaeger"
            )

        from opentelemetry import trace
        
        self.tracer_name = tracer_name
        self._tracer = trace.get_tracer(tracer_name)
        self._current_trace_id: Optional[str] = None
        self._current_span: Optional[Any] = None

    @contextmanager
    def span(
        self,
        operation_name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        """Context manager for creating spans.

        Args:
            operation_name: Name of the operation being traced
            attributes: Optional span attributes/tags

        Yields:
            None
        """
        with self._tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(key, value)

            try:
                yield
            except Exception as exc:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(exc).__name__)
                span.set_attribute("error.message", str(exc))
                raise

    @asynccontextmanager
    async def async_span(
        self,
        operation_name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AsyncGenerator[None, None]:
        """Async context manager for creating spans.

        Args:
            operation_name: Name of the operation being traced
            attributes: Optional span attributes/tags

        Yields:
            None
        """
        with self._tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(key, value)

            try:
                yield
            except Exception as exc:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(exc).__name__)
                span.set_attribute("error.message", str(exc))
                raise

    @contextmanager
    def span_event(
        self,
        event_type: str,
        event_id: str,
        aggregate_id: str,
    ) -> Generator[None, None, None]:
        """Create span for event processing.

        Args:
            event_type: Type of event
            event_id: Event identifier
            aggregate_id: Aggregate identifier

        Yields:
            None
        """
        attributes = {
            "event.type": event_type,
            "event.id": event_id,
            "aggregate.id": aggregate_id,
        }

        with self.span(f"process_event:{event_type}", attributes):
            yield

    @asynccontextmanager
    async def async_span_event(
        self,
        event_type: str,
        event_id: str,
        aggregate_id: str,
    ) -> AsyncGenerator[None, None]:
        """Create async span for event processing.

        Args:
            event_type: Type of event
            event_id: Event identifier
            aggregate_id: Aggregate identifier

        Yields:
            None
        """
        attributes = {
            "event.type": event_type,
            "event.id": event_id,
            "aggregate.id": aggregate_id,
        }

        async with self.async_span(f"process_event:{event_type}", attributes):
            yield

    @contextmanager
    def span_command(
        self,
        command_type: str,
        aggregate_id: str,
    ) -> Generator[None, None, None]:
        """Create span for command handling.

        Args:
            command_type: Type of command
            aggregate_id: Aggregate identifier

        Yields:
            None
        """
        attributes = {
            "command.type": command_type,
            "aggregate.id": aggregate_id,
        }

        with self.span(f"handle_command:{command_type}", attributes):
            yield

    @asynccontextmanager
    async def async_span_command(
        self,
        command_type: str,
        aggregate_id: str,
    ) -> AsyncGenerator[None, None]:
        """Create async span for command handling.

        Args:
            command_type: Type of command
            aggregate_id: Aggregate identifier

        Yields:
            None
        """
        attributes = {
            "command.type": command_type,
            "aggregate.id": aggregate_id,
        }

        async with self.async_span(f"handle_command:{command_type}", attributes):
            yield

    @contextmanager
    def span_saga(
        self,
        saga_type: str,
        saga_id: str,
    ) -> Generator[None, None, None]:
        """Create span for saga execution.

        Args:
            saga_type: Type of saga
            saga_id: Saga identifier

        Yields:
            None
        """
        attributes = {
            "saga.type": saga_type,
            "saga.id": saga_id,
        }

        with self.span(f"execute_saga:{saga_type}", attributes):
            yield

    @asynccontextmanager
    async def async_span_saga(
        self,
        saga_type: str,
        saga_id: str,
    ) -> AsyncGenerator[None, None]:
        """Create async span for saga execution.

        Args:
            saga_type: Type of saga
            saga_id: Saga identifier

        Yields:
            None
        """
        attributes = {
            "saga.type": saga_type,
            "saga.id": saga_id,
        }

        async with self.async_span(f"execute_saga:{saga_type}", attributes):
            yield

    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID.

        Returns:
            Current trace ID or None
        """
        from opentelemetry import trace
        
        span = trace.get_current_span()
        if span and span.is_recording():
            context = span.get_span_context()
            if context:
                return format(context.trace_id, "032x")
        return None

    def set_attribute(self, key: str, value: Any) -> None:
        """Set attribute on current span.

        Args:
            key: Attribute key
            value: Attribute value
        """
        from opentelemetry import trace
        
        span = trace.get_current_span()
        if span and span.is_recording():
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(key, value)

    def add_event(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> None:
        """Add event to current span.

        Args:
            name: Event name
            attributes: Optional event attributes
        """
        from opentelemetry import trace
        
        span = trace.get_current_span()
        if span and span.is_recording():
            if attributes:
                span.add_event(name, attributes)
            else:
                span.add_event(name)


def init_tracing(
    config: TracingConfig | None = None,
    service_name: str = "orchestrix",
    jaeger_agent_host: str = "localhost",
    jaeger_agent_port: int = 6831,
) -> JaegerTracer:
    """Initialize Jaeger distributed tracing.

    Args:
        config: TracingConfig instance or None for defaults
        service_name: Service name for tracing
        jaeger_agent_host: Jaeger agent host
        jaeger_agent_port: Jaeger agent port

    Returns:
        JaegerTracer instance

    Raises:
        ImportError: If Jaeger not installed
    """
    if not HAS_JAEGER:
        raise ImportError(
            "Jaeger not installed. Install with: "
            "pip install opentelemetry-api opentelemetry-exporter-jaeger"
        )

    from opentelemetry import trace
    
    if config is None:
        # Create default config if none provided
        config = TracingConfig(service_name=service_name)

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        exporter = OTLPSpanExporter(
            endpoint=f"{config.jaeger_agent_host}:{config.jaeger_agent_port}",
        )
    except ImportError:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # type: ignore[import-not-found]
        exporter = JaegerExporter(
            agent_host_name=config.jaeger_agent_host,
            agent_port=config.jaeger_agent_port,
        )
    
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    if config is None:
        config = TracingConfig(
            service_name=service_name,
            jaeger_agent_host=jaeger_agent_host,
            jaeger_agent_port=jaeger_agent_port,
        )

    # Create resource with service name
    resource = Resource.create({SERVICE_NAME: config.service_name})

    # Create span processor with exporter
    span_processor = BatchSpanProcessor(exporter)

    # Create and set trace provider
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(trace_provider)

    return JaegerTracer()


def get_tracer() -> JaegerTracer:
    """Get the current tracer instance.

    Returns:
        JaegerTracer instance
    """
    return JaegerTracer()
