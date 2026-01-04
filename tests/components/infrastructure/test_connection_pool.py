"""Tests for PostgreSQL connection pool management."""

import pytest

from orchestrix.infrastructure.connection_pool import PoolConfig, PoolMetrics


class TestPoolConfig:
    """Tests for connection pool configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PoolConfig()
        assert config.min_size == 10
        assert config.max_size == 50
        assert config.max_queries == 50000
        assert config.max_idle_time == 300.0
        assert config.timeout == 30.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = PoolConfig(
            min_size=5,
            max_size=100,
            timeout=60.0,
        )
        assert config.min_size == 5
        assert config.max_size == 100
        assert config.timeout == 60.0

    def test_validate_min_size(self):
        """Test validation of min_size."""
        config = PoolConfig(min_size=0)
        with pytest.raises(ValueError, match="min_size must be at least 1"):
            config.validate()

    def test_validate_max_size(self):
        """Test validation of max_size >= min_size."""
        config = PoolConfig(min_size=50, max_size=10)
        with pytest.raises(ValueError, match="max_size must be >= min_size"):
            config.validate()

    def test_validate_timeout(self):
        """Test validation of timeout."""
        config = PoolConfig(timeout=-1)
        with pytest.raises(ValueError, match="timeout must be positive"):
            config.validate()

    def test_validate_max_idle_time(self):
        """Test validation of max_idle_time."""
        config = PoolConfig(max_idle_time=-1)
        with pytest.raises(ValueError, match="max_idle_time must be non-negative"):
            config.validate()

    def test_validate_success(self):
        """Test validation passes with valid config."""
        config = PoolConfig()
        # Should not raise
        config.validate()

    def test_config_for_high_concurrency(self):
        """Test config for high concurrency scenario."""
        config = PoolConfig(
            min_size=20,
            max_size=200,
            max_queries=100000,
        )
        config.validate()
        assert config.min_size == 20
        assert config.max_size == 200

    def test_config_for_low_concurrency(self):
        """Test config for low concurrency scenario."""
        config = PoolConfig(
            min_size=2,
            max_size=5,
        )
        config.validate()
        assert config.min_size == 2
        assert config.max_size == 5


class TestPoolMetrics:
    """Tests for connection pool metrics."""

    def test_default_metrics(self):
        """Test default metrics values."""
        metrics = PoolMetrics()
        assert metrics.connections_created == 0
        assert metrics.current_size == 0
        assert metrics.idle_size == 0
        assert metrics.acquire_count == 0

    def test_utilization_empty_pool(self):
        """Test utilization calculation for empty pool."""
        metrics = PoolMetrics(current_size=0)
        assert metrics.utilization_percent == 0.0

    def test_utilization_full_pool(self):
        """Test utilization calculation for fully utilized pool."""
        metrics = PoolMetrics(current_size=50, idle_size=0)
        assert metrics.utilization_percent == 100.0

    def test_utilization_partial_pool(self):
        """Test utilization calculation for partially utilized pool."""
        metrics = PoolMetrics(current_size=50, idle_size=30)
        # (50 - 30) / 50 * 100 = 40%
        assert metrics.utilization_percent == 40.0

    def test_healthy_pool(self):
        """Test health check for healthy pool."""
        metrics = PoolMetrics(
            current_size=50,
            idle_size=30,
            acquire_timeout_count=0,
        )
        assert metrics.is_healthy is True

    def test_unhealthy_pool_too_many_timeouts(self):
        """Test health check with too many timeouts."""
        metrics = PoolMetrics(
            acquire_timeout_count=11,
        )
        assert metrics.is_healthy is False

    def test_unhealthy_pool_exhausted(self):
        """Test health check when pool exhausted."""
        metrics = PoolMetrics(
            current_size=150,  # Over 100 threshold
            idle_size=0,
        )
        assert metrics.is_healthy is False

    def test_metrics_copy(self):
        """Test copying metrics."""
        original = PoolMetrics(
            connections_created=10,
            acquire_count=100,
            current_size=50,
        )
        copy = original.copy()

        assert copy.connections_created == 10
        assert copy.acquire_count == 100
        assert copy.current_size == 50

        # Verify it's a copy, not reference
        copy.acquire_count = 200
        assert original.acquire_count == 100

    def test_metrics_with_values(self):
        """Test metrics with various values."""
        metrics = PoolMetrics(
            connections_created=100,
            connections_closed=50,
            current_size=50,
            idle_size=20,
            acquire_count=1000,
            acquire_timeout_count=2,
            acquire_latency_ms=45.5,
        )

        assert metrics.connections_created == 100
        assert metrics.connections_closed == 50
        assert metrics.utilization_percent == 60.0  # (50-20)/50 = 60%
        assert metrics.is_healthy is True


class TestPoolConfigScenarios:
    """Tests for realistic pool configuration scenarios."""

    def test_low_traffic_config(self):
        """Test config for low traffic application."""
        config = PoolConfig(
            min_size=2,
            max_size=10,
            max_idle_time=600.0,  # 10 minutes
        )
        config.validate()
        assert config.min_size == 2

    def test_medium_traffic_config(self):
        """Test config for medium traffic application."""
        config = PoolConfig(
            min_size=10,
            max_size=50,
            max_queries=50000,
        )
        config.validate()
        assert config.min_size == 10

    def test_high_traffic_config(self):
        """Test config for high traffic application."""
        config = PoolConfig(
            min_size=50,
            max_size=200,
            max_idle_time=180.0,  # Shorter idle time
            max_queries=100000,  # More queries per connection
        )
        config.validate()
        assert config.max_size == 200

    def test_microservice_config(self):
        """Test config for microservice with many aggregates."""
        config = PoolConfig(
            min_size=5,
            max_size=30,
            timeout=5.0,  # Shorter timeout
        )
        config.validate()
        assert config.timeout == 5.0


class TestMetricsScenarios:
    """Tests for metrics calculation scenarios."""

    def test_healthy_busy_pool(self):
        """Test metrics for healthy but busy pool."""
        metrics = PoolMetrics(
            current_size=50,
            idle_size=5,
            acquire_count=5000,
            acquire_timeout_count=0,
        )
        # 90% utilization but no timeouts
        assert metrics.utilization_percent == 90.0
        assert metrics.is_healthy is True

    def test_recovering_from_timeouts(self):
        """Test metrics for pool recovering from timeouts."""
        metrics = PoolMetrics(
            current_size=50,
            idle_size=40,
            acquire_timeout_count=5,  # Some but not many
        )
        # Low utilization
        assert metrics.utilization_percent == 20.0
        assert metrics.is_healthy is True

    def test_critical_pool_state(self):
        """Test metrics for pool in critical state."""
        metrics = PoolMetrics(
            current_size=200,  # Over max
            idle_size=0,
            acquire_timeout_count=15,  # Many timeouts
        )
        assert metrics.utilization_percent == 100.0
        assert metrics.is_healthy is False
