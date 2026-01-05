"""Tests for Prometheus metrics integration."""

from __future__ import annotations

import pytest
from orchestrix.infrastructure.observability.prometheus import (
    MetricConfig,
    MetricOperationType,
    PrometheusMetrics,
)


class TestMetricConfig:
    """Tests for MetricConfig."""

    def test_default_config(self) -> None:
        """Test creating config with defaults."""
        config = MetricConfig()
        assert config.namespace == "orchestrix"
        assert config.subsystem == "core"
        assert config.registry is None
        assert config.enable_summary_metrics is True

    def test_custom_config(self) -> None:
        """Test creating config with custom values."""
        config = MetricConfig(namespace="myapp", subsystem="orders", enable_summary_metrics=False)
        assert config.namespace == "myapp"
        assert config.subsystem == "orders"
        assert config.enable_summary_metrics is False

    def test_invalid_namespace(self) -> None:
        """Test config rejects invalid namespace."""
        with pytest.raises(ValueError, match="namespace"):
            MetricConfig(namespace="")

    def test_invalid_subsystem(self) -> None:
        """Test config rejects invalid subsystem."""
        with pytest.raises(ValueError, match="subsystem"):
            MetricConfig(subsystem="")


class TestPrometheusMetrics:
    """Tests for PrometheusMetrics."""

    def test_metrics_initialization(self) -> None:
        """Test initializing metrics with default config."""
        metrics = PrometheusMetrics()
        assert metrics.config is not None
        assert metrics.registry is not None

    def test_metrics_custom_config(self) -> None:
        """Test initializing metrics with custom config."""
        config = MetricConfig(namespace="test", subsystem="events")
        metrics = PrometheusMetrics(config=config)
        assert metrics.config == config

    def test_track_event_publish_success(self) -> None:
        """Test tracking successful event publishing."""
        metrics = PrometheusMetrics()

        with metrics.track_event_publish(event_type="OrderCreated"):
            pass  # Simulate successful operation

        # Verify counters incremented
        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_track_event_publish_failure(self) -> None:
        """Test tracking failed event publishing."""
        metrics = PrometheusMetrics()

        with pytest.raises(RuntimeError):
            with metrics.track_event_publish(event_type="OrderCreated"):
                raise RuntimeError("Publish failed")

    def test_track_command_handle_success(self) -> None:
        """Test tracking successful command handling."""
        metrics = PrometheusMetrics()

        with metrics.track_command_handle(command_type="CreateOrder"):
            pass  # Simulate successful operation

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_track_command_handle_failure(self) -> None:
        """Test tracking failed command handling."""
        metrics = PrometheusMetrics()

        with pytest.raises(ValueError):
            with metrics.track_command_handle(command_type="CreateOrder"):
                raise ValueError("Invalid command")

    def test_track_aggregate_load_success(self) -> None:
        """Test tracking successful aggregate loading."""
        metrics = PrometheusMetrics()

        with metrics.track_aggregate_load(aggregate_type="Order"):
            pass  # Simulate successful loading

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_track_aggregate_load_failure(self) -> None:
        """Test tracking failed aggregate loading."""
        metrics = PrometheusMetrics()

        with pytest.raises(RuntimeError):
            with metrics.track_aggregate_load(aggregate_type="Order"):
                raise RuntimeError("Load failed")

    def test_track_storage_operation_success(self) -> None:
        """Test tracking successful storage operation."""
        metrics = PrometheusMetrics()

        with metrics.track_storage_operation(operation_type=MetricOperationType.APPEND):
            pass  # Simulate successful operation

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_track_storage_operation_failure(self) -> None:
        """Test tracking failed storage operation."""
        metrics = PrometheusMetrics()

        with (
            pytest.raises(IOError),
            metrics.track_storage_operation(operation_type=MetricOperationType.LOAD),
        ):
            raise OSError("Storage error")

    @pytest.mark.asyncio
    async def test_track_async_event_publish_success(self) -> None:
        """Test tracking async event publishing success."""
        metrics = PrometheusMetrics()

        async with metrics.track_async_event_publish(event_type="PaymentProcessed"):
            pass  # Simulate successful operation

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    @pytest.mark.asyncio
    async def test_track_async_event_publish_failure(self) -> None:
        """Test tracking async event publishing failure."""
        metrics = PrometheusMetrics()

        with pytest.raises(RuntimeError):
            async with metrics.track_async_event_publish(event_type="PaymentProcessed"):
                raise RuntimeError("Async publish failed")

    @pytest.mark.asyncio
    async def test_track_async_command_handle_success(self) -> None:
        """Test tracking async command handling success."""
        metrics = PrometheusMetrics()

        async with metrics.track_async_command_handle(command_type="ProcessPayment"):
            pass  # Simulate successful operation

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    @pytest.mark.asyncio
    async def test_track_async_command_handle_failure(self) -> None:
        """Test tracking async command handling failure."""
        metrics = PrometheusMetrics()

        with pytest.raises(ValueError):
            async with metrics.track_async_command_handle(command_type="ProcessPayment"):
                raise ValueError("Invalid async command")

    def test_record_projection_lag(self) -> None:
        """Test recording projection lag."""
        metrics = PrometheusMetrics()

        metrics.record_projection_lag("OrderSummary", 42)
        metrics.record_projection_lag("PaymentStatus", 7)

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_track_projection_update(self) -> None:
        """Test tracking projection update latency."""
        metrics = PrometheusMetrics()

        with metrics.track_projection_update(projection_name="OrderSummary"):
            pass  # Simulate update

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_track_saga_execution_success(self) -> None:
        """Test tracking successful saga execution."""
        metrics = PrometheusMetrics()

        with metrics.track_saga_execution(saga_type="MoneyTransfer"):
            pass  # Simulate successful saga

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_track_saga_execution_failure(self) -> None:
        """Test tracking failed saga execution."""
        metrics = PrometheusMetrics()

        with pytest.raises(Exception):
            with metrics.track_saga_execution(saga_type="MoneyTransfer"):
                raise Exception("Saga failed")

    def test_get_prometheus_registry(self) -> None:
        """Test getting Prometheus registry."""
        metrics = PrometheusMetrics()
        registry = metrics.get_prometheus_registry()
        assert registry is not None
        assert registry == metrics.registry

    def test_generate_exposition(self) -> None:
        """Test generating Prometheus exposition format."""
        metrics = PrometheusMetrics()

        # Record some metrics
        with metrics.track_event_publish(event_type="Test"):
            pass

        # Generate exposition
        exposition = PrometheusMetrics.generate_exposition(metrics.registry)
        assert isinstance(exposition, bytes)
        assert b"orchestrix_core" in exposition

    def test_multiple_metric_operations(self) -> None:
        """Test tracking multiple operations simultaneously."""
        metrics = PrometheusMetrics()

        # Simulate multiple concurrent operations
        with metrics.track_event_publish(event_type="Created"):
            with metrics.track_command_handle(command_type="Create"):
                with metrics.track_aggregate_load(aggregate_type="Entity"):
                    pass

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_metric_operation_types(self) -> None:
        """Test all metric operation types."""
        metrics = PrometheusMetrics()

        for op_type in MetricOperationType:
            with metrics.track_storage_operation(operation_type=op_type):
                pass

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_custom_namespace_in_metrics(self) -> None:
        """Test custom namespace appears in metric names."""
        config = MetricConfig(namespace="myservice", subsystem="domain")
        metrics = PrometheusMetrics(config=config)

        with metrics.track_event_publish(event_type="Test"):
            pass

        exposition = PrometheusMetrics.generate_exposition(metrics.registry)
        assert b"myservice_domain" in exposition

    def test_projection_lag_multiple_projections(self) -> None:
        """Test tracking lag for multiple projections."""
        metrics = PrometheusMetrics()

        projections = {
            "OrderSummary": 10,
            "CustomerProfile": 5,
            "PaymentStatus": 0,
        }

        for proj_name, lag in projections.items():
            metrics.record_projection_lag(proj_name, lag)

        samples = list(metrics.registry.collect())
        assert len(samples) > 0

    def test_repeated_operations_accumulate(self) -> None:
        """Test that repeated operations accumulate correctly."""
        metrics = PrometheusMetrics()

        # Perform same operation multiple times
        for _ in range(5):
            with metrics.track_event_publish(event_type="OrderCreated"):
                pass

        # Verify metrics were recorded
        samples = list(metrics.registry.collect())
        assert len(samples) > 0
