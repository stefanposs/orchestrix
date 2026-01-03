"""Observability instrumentation for Orchestrix.

Provides hooks for metrics, tracing, and monitoring in event sourcing operations.
Designed for integration with OpenTelemetry, Prometheus, Jaeger, and other observability tools.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


class MetricType:
    """Metric type constants."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    DURATION = "duration"


@dataclass
class MetricValue:
    """Metric value with metadata."""

    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: dict[str, str] = field(default_factory=dict)
    metric_type: str = MetricType.COUNTER


@dataclass
class TraceSpan:
    """Distributed trace span."""

    operation: str
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: str = "pending"
    attributes: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def end(self) -> None:
        """Mark span as ended."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        if self.status == "pending":
            self.status = "ok"

    def set_error(self, error: str) -> None:
        """Mark span as errored."""
        self.error = error
        self.status = "error"
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


class MetricsProvider(ABC):
    """Abstract base for metrics collection.

    Implement to integrate with your observability backend (Prometheus, StatsD, etc).
    """

    @abstractmethod
    def record_metric(self, metric: MetricValue) -> None:
        """Record a metric value.

        Args:
            metric: Metric to record
        """
        ...

    @abstractmethod
    def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record counter metric.

        Args:
            name: Metric name
            value: Increment amount
            labels: Optional labels
        """
        ...

    @abstractmethod
    def gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record gauge metric.

        Args:
            name: Metric name
            value: Current value
            labels: Optional labels
        """
        ...

    @abstractmethod
    def histogram(
        self,
        name: str,
        value: float,
        unit: str = "",
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record histogram metric.

        Args:
            name: Metric name
            value: Sample value
            unit: Unit of measurement
            labels: Optional labels
        """
        ...


class NoOpMetricsProvider(MetricsProvider):
    """No-op metrics provider (default)."""

    def record_metric(self, metric: MetricValue) -> None:
        """No-op implementation."""

    def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """No-op implementation."""

    def gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """No-op implementation."""

    def histogram(
        self,
        name: str,
        value: float,
        unit: str = "",
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """No-op implementation."""


class TracingProvider(ABC):
    """Abstract base for distributed tracing.

    Implement to integrate with your tracing backend (Jaeger, Zipkin, etc).
    """

    @abstractmethod
    def start_span(self, operation: str) -> TraceSpan:
        """Start a new trace span.

        Args:
            operation: Operation name

        Returns:
            TraceSpan instance
        """
        ...

    @abstractmethod
    def end_span(self, span: TraceSpan) -> None:
        """End a trace span.

        Args:
            span: TraceSpan to end
        """
        ...


class NoOpTracingProvider(TracingProvider):
    """No-op tracing provider (default)."""

    def start_span(self, operation: str) -> TraceSpan:
        """Create span but don't export."""
        return TraceSpan(operation=operation)

    def end_span(self, span: TraceSpan) -> None:
        """No-op implementation."""
        span.end()


class ObservabilityHooks:
    """Central registry for observability hooks.

    Enables instrumentation of event sourcing operations without coupling
    to specific observability implementations.
    """

    def __init__(
        self,
        metrics_provider: Optional[MetricsProvider] = None,
        tracing_provider: Optional[TracingProvider] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize observability hooks.

        Args:
            metrics_provider: Metrics implementation (defaults to no-op)
            tracing_provider: Tracing implementation (defaults to no-op)
            logger: Logger instance (defaults to root logger)
        """
        self.metrics = metrics_provider or NoOpMetricsProvider()
        self.tracing = tracing_provider or NoOpTracingProvider()
        self.logger = logger or logging.getLogger("orchestrix.observability")

        # Event sourcing hooks
        self._event_stored_hooks: list[Callable[[str, int], None]] = []
        self._event_loaded_hooks: list[Callable[[str, int], None]] = []
        self._event_replayed_hooks: list[Callable[[str, str], None]] = []
        self._snapshot_saved_hooks: list[Callable[[str, int], None]] = []
        self._snapshot_loaded_hooks: list[Callable[[str, int], None]] = []
        self._aggregate_error_hooks: list[Callable[[str, str], None]] = []

    # === Metrics ===

    def record_event_stored(self, aggregate_id: str, version: int) -> None:
        """Record event storage.

        Args:
            aggregate_id: Aggregate identifier
            version: Event version
        """
        self.metrics.counter(
            "orchestrix.events.stored",
            labels={"aggregate_id": aggregate_id},
        )
        for hook in self._event_stored_hooks:
            hook(aggregate_id, version)

    def record_event_loaded(self, aggregate_id: str, count: int) -> None:
        """Record events loaded.

        Args:
            aggregate_id: Aggregate identifier
            count: Number of events loaded
        """
        self.metrics.histogram(
            "orchestrix.events.loaded.count",
            count,
            labels={"aggregate_id": aggregate_id},
        )
        for hook in self._event_loaded_hooks:
            hook(aggregate_id, count)

    def record_event_replayed(self, aggregate_id: str, event_type: str) -> None:
        """Record event replay.

        Args:
            aggregate_id: Aggregate identifier
            event_type: Type of event replayed
        """
        self.metrics.counter(
            "orchestrix.events.replayed",
            labels={"aggregate_id": aggregate_id, "event_type": event_type},
        )
        for hook in self._event_replayed_hooks:
            hook(aggregate_id, event_type)

    def record_snapshot_saved(self, aggregate_id: str, version: int) -> None:
        """Record snapshot save.

        Args:
            aggregate_id: Aggregate identifier
            version: Snapshot version
        """
        self.metrics.counter(
            "orchestrix.snapshots.saved",
            labels={"aggregate_id": aggregate_id},
        )
        for hook in self._snapshot_saved_hooks:
            hook(aggregate_id, version)

    def record_snapshot_loaded(self, aggregate_id: str, version: int) -> None:
        """Record snapshot load.

        Args:
            aggregate_id: Aggregate identifier
            version: Snapshot version
        """
        self.metrics.counter(
            "orchestrix.snapshots.loaded",
            labels={"aggregate_id": aggregate_id},
        )
        for hook in self._snapshot_loaded_hooks:
            hook(aggregate_id, version)

    # === Tracing ===

    def start_event_store_operation(self, operation: str) -> TraceSpan:
        """Start tracing an event store operation.

        Args:
            operation: Operation name (load, save, etc)

        Returns:
            TraceSpan instance
        """
        return self.tracing.start_span(f"event_store.{operation}")

    def end_event_store_operation(self, span: TraceSpan) -> None:
        """End event store operation trace.

        Args:
            span: TraceSpan to end
        """
        self.tracing.end_span(span)

    # === Error Tracking ===

    def record_aggregate_error(self, aggregate_id: str, error: str) -> None:
        """Record aggregate processing error.

        Args:
            aggregate_id: Aggregate identifier
            error: Error message
        """
        self.metrics.counter(
            "orchestrix.aggregate.errors",
            labels={"aggregate_id": aggregate_id, "error_type": type(error).__name__},
        )
        for hook in self._aggregate_error_hooks:
            hook(aggregate_id, error)
        self.logger.warning(f"Aggregate error: {error}", extra={"aggregate_id": aggregate_id})

    # === Hook Registration ===

    def on_event_stored(self, callback: Callable[[str, int], None]) -> None:
        """Register callback for event storage.

        Args:
            callback: Function(aggregate_id, version)
        """
        self._event_stored_hooks.append(callback)

    def on_event_loaded(self, callback: Callable[[str, int], None]) -> None:
        """Register callback for events loaded.

        Args:
            callback: Function(aggregate_id, count)
        """
        self._event_loaded_hooks.append(callback)

    def on_event_replayed(self, callback: Callable[[str, str], None]) -> None:
        """Register callback for event replay.

        Args:
            callback: Function(aggregate_id, event_type)
        """
        self._event_replayed_hooks.append(callback)

    def on_snapshot_saved(self, callback: Callable[[str, int], None]) -> None:
        """Register callback for snapshot save.

        Args:
            callback: Function(aggregate_id, version)
        """
        self._snapshot_saved_hooks.append(callback)

    def on_snapshot_loaded(self, callback: Callable[[str, int], None]) -> None:
        """Register callback for snapshot load.

        Args:
            callback: Function(aggregate_id, version)
        """
        self._snapshot_loaded_hooks.append(callback)

    def on_aggregate_error(self, callback: Callable[[str, str], None]) -> None:
        """Register callback for aggregate errors.

        Args:
            callback: Function(aggregate_id, error_message)
        """
        self._aggregate_error_hooks.append(callback)


# Global observability instance
_global_observability: Optional[ObservabilityHooks] = None


def get_observability() -> ObservabilityHooks:
    """Get global observability instance.

    Returns:
        ObservabilityHooks instance
    """
    global _global_observability
    if _global_observability is None:
        _global_observability = ObservabilityHooks()
    return _global_observability


def set_observability(hooks: ObservabilityHooks) -> None:
    """Set global observability instance.

    Args:
        hooks: ObservabilityHooks instance to use globally
    """
    global _global_observability
    _global_observability = hooks


def init_observability(
    metrics_provider: Optional[MetricsProvider] = None,
    tracing_provider: Optional[TracingProvider] = None,
    logger: Optional[logging.Logger] = None,
) -> ObservabilityHooks:
    """Initialize and set global observability.

    Args:
        metrics_provider: Metrics backend implementation
        tracing_provider: Tracing backend implementation
        logger: Logger instance

    Returns:
        Initialized ObservabilityHooks instance
    """
    hooks = ObservabilityHooks(
        metrics_provider=metrics_provider,
        tracing_provider=tracing_provider,
        logger=logger,
    )
    set_observability(hooks)
    return hooks
