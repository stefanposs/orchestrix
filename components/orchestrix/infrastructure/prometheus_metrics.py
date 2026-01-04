"""Prometheus metrics integration for event sourcing observability.

This module provides production-grade Prometheus metrics for monitoring
event sourcing systems, including events, commands, aggregates, and
storage operations.

Key metrics:
- Events: Count, types, processing time
- Commands: Success/failure rates, latency
- Aggregates: Load time, rebuild time, state changes
- Storage: Operation latency, success/failure rates
- Projections: Event lag, update latency

Example:
    from orchestrix.infrastructure.prometheus_metrics import PrometheusMetrics

    metrics = PrometheusMetrics(namespace="myapp", subsystem="events")

    # Track event publishing
    with metrics.track_event_publish():
        await event_store.append_events(aggregate_id, events)

    # Track command handling
    with metrics.track_command_handle(command_type="CreateOrder"):
        result = await command_handler(command)

    # Get Prometheus registry for exposition
    registry = metrics.get_prometheus_registry()
    exposition_format = PrometheusMetrics.generate_exposition(registry)
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator, Generator

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    # Provide dummy types for type checking
    CollectorRegistry = object  # type: ignore[assignment,misc]
    Counter = object  # type: ignore[assignment,misc]
    Gauge = object  # type: ignore[assignment,misc]
    Histogram = object  # type: ignore[assignment,misc]
    
    def generate_latest(registry: Any) -> bytes:  # type: ignore[misc]
        return b""


class MetricOperationType(str, Enum):
    """Types of operations tracked by metrics."""

    APPEND = "append"
    LOAD = "load"
    DELETE = "delete"
    UPDATE = "update"
    QUERY = "query"


@dataclass(frozen=True)
class MetricConfig:
    """Configuration for Prometheus metrics.

    Attributes:
        namespace: Namespace for metrics (e.g., "myapp")
        subsystem: Subsystem name (e.g., "events")
        registry: Optional CollectorRegistry (uses default if None)
        enable_summary_metrics: Whether to track summary statistics
    """

    namespace: str = "orchestrix"
    subsystem: str = "core"
    registry: CollectorRegistry | None = None
    enable_summary_metrics: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.namespace or not isinstance(self.namespace, str):
            raise ValueError("namespace must be non-empty string")
        if not self.subsystem or not isinstance(self.subsystem, str):
            raise ValueError("subsystem must be non-empty string")


class PrometheusMetrics:
    """Prometheus metrics provider for event sourcing systems.

    Tracks events, commands, aggregates, and storage operations with
    comprehensive visibility into system behavior and performance.

    Requires prometheus-client library:
        pip install prometheus-client
    """

    def __init__(self, config: MetricConfig | None = None) -> None:
        """Initialize Prometheus metrics.

        Args:
            config: MetricConfig instance or None for defaults
        """
        if not HAS_PROMETHEUS:
            raise ImportError(
                "prometheus-client not installed. "
                "Install with: pip install prometheus-client"
            )

        self.config = config or MetricConfig()
        self.registry = self.config.registry or CollectorRegistry()

        # Construct metric prefix
        prefix = f"{self.config.namespace}_{self.config.subsystem}"

        # Event metrics
        self.events_total = Counter(
            f"{prefix}_events_total",
            "Total events published",
            ["event_type", "status"],
            registry=self.registry,
        )
        self.events_processing_seconds = Histogram(
            f"{prefix}_events_processing_seconds",
            "Event processing time in seconds",
            ["event_type"],
            registry=self.registry,
        )

        # Command metrics
        self.commands_total = Counter(
            f"{prefix}_commands_total",
            "Total commands processed",
            ["command_type", "status"],
            registry=self.registry,
        )
        self.commands_latency_seconds = Histogram(
            f"{prefix}_commands_latency_seconds",
            "Command processing latency in seconds",
            ["command_type"],
            registry=self.registry,
        )

        # Aggregate metrics
        self.aggregates_loaded_total = Counter(
            f"{prefix}_aggregates_loaded_total",
            "Total aggregates loaded",
            ["aggregate_type"],
            registry=self.registry,
        )
        self.aggregates_load_time_seconds = Histogram(
            f"{prefix}_aggregates_load_time_seconds",
            "Time to load aggregate in seconds",
            ["aggregate_type"],
            registry=self.registry,
        )
        self.aggregates_in_memory = Gauge(
            f"{prefix}_aggregates_in_memory",
            "Number of aggregates currently in memory",
            ["aggregate_type"],
            registry=self.registry,
        )

        # Storage metrics
        self.storage_operations_total = Counter(
            f"{prefix}_storage_operations_total",
            "Total storage operations",
            ["operation_type", "status"],
            registry=self.registry,
        )
        self.storage_operation_seconds = Histogram(
            f"{prefix}_storage_operation_seconds",
            "Storage operation duration in seconds",
            ["operation_type"],
            registry=self.registry,
        )

        # Projection metrics
        self.projection_events_behind = Gauge(
            f"{prefix}_projection_events_behind",
            "Number of unprocessed events in projections",
            ["projection_name"],
            registry=self.registry,
        )
        self.projection_update_seconds = Histogram(
            f"{prefix}_projection_update_seconds",
            "Projection update latency in seconds",
            ["projection_name"],
            registry=self.registry,
        )

        # Saga metrics
        self.saga_executions_total = Counter(
            f"{prefix}_saga_executions_total",
            "Total saga executions",
            ["saga_type", "status"],
            registry=self.registry,
        )
        self.saga_duration_seconds = Histogram(
            f"{prefix}_saga_duration_seconds",
            "Saga execution duration in seconds",
            ["saga_type"],
            registry=self.registry,
        )

    @contextmanager
    def track_event_publish(
        self, event_type: str = "unknown"
    ) -> Generator[None, None, None]:
        """Context manager to track event publishing.

        Args:
            event_type: Type of event being published

        Yields:
            None
        """
        timer = self.events_processing_seconds.labels(event_type=event_type).time()

        try:
            with timer:
                yield
            self.events_total.labels(event_type=event_type, status="success").inc()
        except Exception:
            self.events_total.labels(event_type=event_type, status="error").inc()
            raise

    @contextmanager
    def track_command_handle(
        self, command_type: str = "unknown"
    ) -> Generator[None, None, None]:
        """Context manager to track command handling.

        Args:
            command_type: Type of command being handled

        Yields:
            None
        """
        timer = self.commands_latency_seconds.labels(
            command_type=command_type
        ).time()

        try:
            with timer:
                yield
            self.commands_total.labels(command_type=command_type, status="success").inc()
        except Exception:
            self.commands_total.labels(command_type=command_type, status="error").inc()
            raise

    @contextmanager
    def track_aggregate_load(
        self, aggregate_type: str = "unknown"
    ) -> Generator[None, None, None]:
        """Context manager to track aggregate loading.

        Args:
            aggregate_type: Type of aggregate being loaded

        Yields:
            None
        """
        timer = self.aggregates_load_time_seconds.labels(
            aggregate_type=aggregate_type
        ).time()

        self.aggregates_in_memory.labels(aggregate_type=aggregate_type).inc()

        try:
            with timer:
                yield
            self.aggregates_loaded_total.labels(aggregate_type=aggregate_type).inc()
        except Exception:
            self.aggregates_in_memory.labels(aggregate_type=aggregate_type).dec()
            raise

    @contextmanager
    def track_storage_operation(
        self, operation_type: MetricOperationType = MetricOperationType.APPEND
    ) -> Generator[None, None, None]:
        """Context manager to track storage operations.

        Args:
            operation_type: Type of storage operation

        Yields:
            None
        """
        timer = self.storage_operation_seconds.labels(
            operation_type=operation_type.value
        ).time()

        try:
            with timer:
                yield
            self.storage_operations_total.labels(
                operation_type=operation_type.value, status="success"
            ).inc()
        except Exception:
            self.storage_operations_total.labels(
                operation_type=operation_type.value, status="error"
            ).inc()
            raise

    @asynccontextmanager
    async def track_async_event_publish(
        self, event_type: str = "unknown"
    ) -> AsyncGenerator[None, None]:
        """Async context manager to track event publishing.

        Args:
            event_type: Type of event being published

        Yields:
            None
        """
        timer = self.events_processing_seconds.labels(event_type=event_type).time()

        try:
            with timer:
                yield
            self.events_total.labels(event_type=event_type, status="success").inc()
        except Exception:
            self.events_total.labels(event_type=event_type, status="error").inc()
            raise

    @asynccontextmanager
    async def track_async_command_handle(
        self, command_type: str = "unknown"
    ) -> AsyncGenerator[None, None]:
        """Async context manager to track command handling.

        Args:
            command_type: Type of command being handled

        Yields:
            None
        """
        timer = self.commands_latency_seconds.labels(
            command_type=command_type
        ).time()

        try:
            with timer:
                yield
            self.commands_total.labels(command_type=command_type, status="success").inc()
        except Exception:
            self.commands_total.labels(command_type=command_type, status="error").inc()
            raise

    def record_projection_lag(
        self, projection_name: str, events_behind: int
    ) -> None:
        """Record the number of unprocessed events in a projection.

        Args:
            projection_name: Name of the projection
            events_behind: Number of events behind
        """
        self.projection_events_behind.labels(projection_name=projection_name).set(
            events_behind
        )

    @contextmanager
    def track_projection_update(
        self, projection_name: str = "unknown"
    ) -> Generator[None, None, None]:
        """Context manager to track projection update latency.

        Args:
            projection_name: Name of the projection

        Yields:
            None
        """
        timer = self.projection_update_seconds.labels(
            projection_name=projection_name
        ).time()

        try:
            with timer:
                yield
        except Exception:
            raise

    @contextmanager
    def track_saga_execution(
        self, saga_type: str = "unknown"
    ) -> Generator[None, None, None]:
        """Context manager to track saga execution.

        Args:
            saga_type: Type of saga being executed

        Yields:
            None
        """
        timer = self.saga_duration_seconds.labels(saga_type=saga_type).time()

        try:
            with timer:
                yield
            self.saga_executions_total.labels(saga_type=saga_type, status="success").inc()
        except Exception:
            self.saga_executions_total.labels(saga_type=saga_type, status="error").inc()
            raise

    def get_prometheus_registry(self) -> CollectorRegistry:
        """Get the Prometheus CollectorRegistry for exposition.

        Returns:
            CollectorRegistry instance
        """
        return self.registry

    @staticmethod
    def generate_exposition(registry: CollectorRegistry) -> bytes:
        """Generate Prometheus exposition format from registry.

        Args:
            registry: CollectorRegistry instance

        Returns:
            Prometheus text exposition format as bytes
        """
        return generate_latest(registry)
