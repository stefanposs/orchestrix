"""Tests for observability instrumentation.

Tests metrics, tracing, and monitoring hooks.
"""

import logging
from unittest.mock import MagicMock

from orchestrix.core.common.observability import (
    MetricsProvider,
    MetricType,
    MetricValue,
    NoOpMetricsProvider,
    NoOpTracingProvider,
    ObservabilityHooks,
    TraceSpan,
    TracingProvider,
    get_observability,
    init_observability,
    set_observability,
)


class MockMetricsProvider(MetricsProvider):
    """Mock metrics provider for testing."""

    def __init__(self) -> None:
        """Initialize mock."""
        self.metrics: list[MetricValue] = []
        self.counters: list[tuple[str, float, dict[str, str] | None]] = []
        self.gauges: list[tuple[str, float, dict[str, str] | None]] = []
        self.histograms: list[tuple[str, float, str, dict[str, str] | None]] = []

    def record_metric(self, metric: MetricValue) -> None:
        """Record metric."""
        self.metrics.append(metric)

    def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record counter."""
        self.counters.append((name, value, labels))

    def gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record gauge."""
        self.gauges.append((name, value, labels))

    def histogram(
        self,
        name: str,
        value: float,
        unit: str = "",
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record histogram."""
        self.histograms.append((name, value, unit, labels))


class MockTracingProvider(TracingProvider):
    """Mock tracing provider for testing."""

    def __init__(self) -> None:
        """Initialize mock."""
        self.spans: list[TraceSpan] = []

    def start_span(self, operation: str) -> TraceSpan:
        """Start span."""
        span = TraceSpan(operation=operation)
        self.spans.append(span)
        return span

    def end_span(self, span: TraceSpan) -> None:
        """End span."""
        span.end()


class TestMetricValue:
    """Tests for MetricValue dataclass."""

    def test_metric_value_creation(self) -> None:
        """Test creating metric value."""
        metric = MetricValue(
            name="test.metric",
            value=42.0,
            unit="count",
            labels={"tag": "value"},
        )

        assert metric.name == "test.metric"
        assert metric.value == 42.0
        assert metric.unit == "count"
        assert metric.labels == {"tag": "value"}
        assert metric.metric_type == MetricType.COUNTER

    def test_metric_value_with_defaults(self) -> None:
        """Test metric value with defaults."""
        metric = MetricValue(name="test", value=1.0)

        assert metric.timestamp is not None
        assert metric.labels == {}
        assert metric.metric_type == MetricType.COUNTER


class TestTraceSpan:
    """Tests for TraceSpan."""

    def test_span_creation(self) -> None:
        """Test creating span."""
        span = TraceSpan(operation="test.op")

        assert span.operation == "test.op"
        assert span.status == "pending"
        assert span.error is None

    def test_span_end(self) -> None:
        """Test ending span."""
        span = TraceSpan(operation="test.op")
        span.end()

        assert span.status == "ok"
        assert span.end_time is not None
        assert span.duration_ms > 0

    def test_span_error(self) -> None:
        """Test span with error."""
        span = TraceSpan(operation="test.op")
        span.set_error("Something went wrong")

        assert span.status == "error"
        assert span.error == "Something went wrong"
        assert span.end_time is not None


class TestNoOpMetricsProvider:
    """Tests for NoOpMetricsProvider."""

    def test_counter_noop(self) -> None:
        """Test counter does nothing."""
        provider = NoOpMetricsProvider()
        provider.counter("test", 1.0)  # Should not raise

    def test_gauge_noop(self) -> None:
        """Test gauge does nothing."""
        provider = NoOpMetricsProvider()
        provider.gauge("test", 42.0)  # Should not raise

    def test_histogram_noop(self) -> None:
        """Test histogram does nothing."""
        provider = NoOpMetricsProvider()
        provider.histogram("test", 100.0)  # Should not raise

    def test_record_metric_noop(self) -> None:
        """Test record_metric does nothing."""
        provider = NoOpMetricsProvider()
        metric = MetricValue(name="test", value=1.0)
        provider.record_metric(metric)  # Should not raise


class TestNoOpTracingProvider:
    """Tests for NoOpTracingProvider."""

    def test_start_span(self) -> None:
        """Test starting span."""
        provider = NoOpTracingProvider()
        span = provider.start_span("test.op")

        assert span.operation == "test.op"
        assert span.status == "pending"

    def test_end_span(self) -> None:
        """Test ending span."""
        provider = NoOpTracingProvider()
        span = provider.start_span("test.op")
        provider.end_span(span)

        assert span.status == "ok"
        assert span.duration_ms > 0


class TestObservabilityHooks:
    """Tests for ObservabilityHooks."""

    def test_creation_with_defaults(self) -> None:
        """Test creating hooks with defaults."""
        hooks = ObservabilityHooks()

        assert isinstance(hooks.metrics, NoOpMetricsProvider)
        assert isinstance(hooks.tracing, NoOpTracingProvider)
        assert hooks.logger is not None

    def test_creation_with_custom_providers(self) -> None:
        """Test creating hooks with custom providers."""
        metrics = MockMetricsProvider()
        tracing = MockTracingProvider()
        logger = logging.getLogger("test")

        hooks = ObservabilityHooks(
            metrics_provider=metrics,
            tracing_provider=tracing,
            logger=logger,
        )

        assert hooks.metrics is metrics
        assert hooks.tracing is tracing
        assert hooks.logger is logger

    def test_record_event_stored(self) -> None:
        """Test recording event stored."""
        metrics = MockMetricsProvider()
        hooks = ObservabilityHooks(metrics_provider=metrics)

        hooks.record_event_stored("agg-1", 1)

        assert len(metrics.counters) == 1
        assert metrics.counters[0][0] == "orchestrix.events.stored"
        assert metrics.counters[0][2] == {"aggregate_id": "agg-1"}

    def test_record_event_loaded(self) -> None:
        """Test recording events loaded."""
        metrics = MockMetricsProvider()
        hooks = ObservabilityHooks(metrics_provider=metrics)

        hooks.record_event_loaded("agg-1", 5)

        assert len(metrics.histograms) == 1
        assert metrics.histograms[0][0] == "orchestrix.events.loaded.count"
        assert metrics.histograms[0][1] == 5

    def test_record_event_replayed(self) -> None:
        """Test recording event replay."""
        metrics = MockMetricsProvider()
        hooks = ObservabilityHooks(metrics_provider=metrics)

        hooks.record_event_replayed("agg-1", "UserCreated")

        assert len(metrics.counters) == 1
        assert metrics.counters[0][0] == "orchestrix.events.replayed"

    def test_record_snapshot_saved(self) -> None:
        """Test recording snapshot save."""
        metrics = MockMetricsProvider()
        hooks = ObservabilityHooks(metrics_provider=metrics)

        hooks.record_snapshot_saved("agg-1", 10)

        assert len(metrics.counters) == 1
        assert metrics.counters[0][0] == "orchestrix.snapshots.saved"

    def test_record_snapshot_loaded(self) -> None:
        """Test recording snapshot load."""
        metrics = MockMetricsProvider()
        hooks = ObservabilityHooks(metrics_provider=metrics)

        hooks.record_snapshot_loaded("agg-1", 10)

        assert len(metrics.counters) == 1
        assert metrics.counters[0][0] == "orchestrix.snapshots.loaded"

    def test_start_and_end_event_store_operation(self) -> None:
        """Test tracing event store operation."""
        tracing = MockTracingProvider()
        hooks = ObservabilityHooks(tracing_provider=tracing)

        span = hooks.start_event_store_operation("load")
        assert span.operation == "event_store.load"
        assert span.status == "pending"

        hooks.end_event_store_operation(span)
        assert span.status == "ok"

    def test_record_aggregate_error(self) -> None:
        """Test recording aggregate error."""
        metrics = MockMetricsProvider()
        hooks = ObservabilityHooks(metrics_provider=metrics)

        hooks.record_aggregate_error("agg-1", "Validation failed")

        assert len(metrics.counters) == 1
        assert metrics.counters[0][0] == "orchestrix.aggregate.errors"


class TestHookCallbacks:
    """Tests for hook callback registration."""

    def test_event_stored_callback(self) -> None:
        """Test event_stored callback."""
        hooks = ObservabilityHooks()
        callback = MagicMock()

        hooks.on_event_stored(callback)
        hooks.record_event_stored("agg-1", 1)

        callback.assert_called_once_with("agg-1", 1)

    def test_event_loaded_callback(self) -> None:
        """Test event_loaded callback."""
        hooks = ObservabilityHooks()
        callback = MagicMock()

        hooks.on_event_loaded(callback)
        hooks.record_event_loaded("agg-1", 5)

        callback.assert_called_once_with("agg-1", 5)

    def test_event_replayed_callback(self) -> None:
        """Test event_replayed callback."""
        hooks = ObservabilityHooks()
        callback = MagicMock()

        hooks.on_event_replayed(callback)
        hooks.record_event_replayed("agg-1", "EventType")

        callback.assert_called_once_with("agg-1", "EventType")

    def test_snapshot_saved_callback(self) -> None:
        """Test snapshot_saved callback."""
        hooks = ObservabilityHooks()
        callback = MagicMock()

        hooks.on_snapshot_saved(callback)
        hooks.record_snapshot_saved("agg-1", 10)

        callback.assert_called_once_with("agg-1", 10)

    def test_snapshot_loaded_callback(self) -> None:
        """Test snapshot_loaded callback."""
        hooks = ObservabilityHooks()
        callback = MagicMock()

        hooks.on_snapshot_loaded(callback)
        hooks.record_snapshot_loaded("agg-1", 10)

        callback.assert_called_once_with("agg-1", 10)

    def test_aggregate_error_callback(self) -> None:
        """Test aggregate_error callback."""
        hooks = ObservabilityHooks()
        callback = MagicMock()

        hooks.on_aggregate_error(callback)
        hooks.record_aggregate_error("agg-1", "Error message")

        callback.assert_called_once_with("agg-1", "Error message")

    def test_multiple_callbacks(self) -> None:
        """Test multiple callbacks for same event."""
        hooks = ObservabilityHooks()
        callback1 = MagicMock()
        callback2 = MagicMock()

        hooks.on_event_stored(callback1)
        hooks.on_event_stored(callback2)
        hooks.record_event_stored("agg-1", 1)

        callback1.assert_called_once_with("agg-1", 1)
        callback2.assert_called_once_with("agg-1", 1)


class TestGlobalObservability:
    """Tests for global observability functions."""

    def test_get_observability_default(self) -> None:
        """Test getting default observability."""
        set_observability(ObservabilityHooks())  # Reset
        obs = get_observability()

        assert obs is not None
        assert isinstance(obs.metrics, NoOpMetricsProvider)

    def test_set_observability(self) -> None:
        """Test setting observability."""
        metrics = MockMetricsProvider()
        hooks = ObservabilityHooks(metrics_provider=metrics)

        set_observability(hooks)
        obs = get_observability()

        assert obs is hooks
        assert isinstance(obs.metrics, MockMetricsProvider)

    def test_init_observability(self) -> None:
        """Test initializing observability."""
        metrics = MockMetricsProvider()
        tracing = MockTracingProvider()

        obs = init_observability(
            metrics_provider=metrics,
            tracing_provider=tracing,
        )

        assert obs.metrics is metrics
        assert obs.tracing is tracing
        assert get_observability() is obs
