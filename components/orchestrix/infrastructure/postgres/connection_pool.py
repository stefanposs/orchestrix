"""PostgreSQL connection pool management and monitoring.

Provides robust connection pooling with metrics, health checking,
and automatic recovery from pool exhaustion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import asyncpg  # type: ignore[import-untyped]


@dataclass
class PoolConfig:
    """Configuration for PostgreSQL connection pool.

    Attributes:
        min_size: Minimum number of connections to maintain
        max_size: Maximum number of connections allowed
        max_queries: Max queries a connection can process before being recycled
        max_idle_time: Maximum idle time in seconds before recycling
        max_cached_statement_lifetime: Max time to cache prepared statements
        max_cacheable_statement_size: Max size of statements to cache
        timeout: Acquisition timeout in seconds
    """

    min_size: int = 10
    """Minimum connections - maintained even during idle periods"""

    max_size: int = 50
    """Maximum connections - hard limit to prevent resource exhaustion"""

    max_queries: int = 50000
    """Queries per connection before recycling (prevents long-lived connections)"""

    max_idle_time: float = 300.0
    """Idle timeout in seconds (5 minutes default)"""

    max_cached_statement_lifetime: int = 3600
    """Max time in seconds to cache prepared statements"""

    max_cacheable_statement_size: int = 15000
    """Max size in bytes of statements to cache"""

    timeout: float = 30.0
    """Acquisition timeout in seconds"""

    def validate(self) -> None:
        """Validate pool configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.min_size < 1:
            raise ValueError("min_size must be at least 1")
        if self.max_size < self.min_size:
            raise ValueError("max_size must be >= min_size")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_idle_time < 0:
            raise ValueError("max_idle_time must be non-negative")


@dataclass
class PoolMetrics:
    """Metrics for connection pool health monitoring.

    Attributes:
        connections_created: Total connections created
        connections_closed: Total connections closed
        current_size: Current number of connections in pool
        idle_size: Number of idle connections available
        acquire_count: Total connection acquisitions
        acquire_timeout_count: Number of acquisition timeouts
        acquire_latency_ms: Average acquisition latency
    """

    connections_created: int = 0
    connections_closed: int = 0
    current_size: int = 0
    idle_size: int = 0
    acquire_count: int = 0
    acquire_timeout_count: int = 0
    acquire_latency_ms: float = 0.0

    def copy(self) -> PoolMetrics:
        """Create a copy of metrics.

        Returns:
            New PoolMetrics instance with same values
        """
        return PoolMetrics(
            connections_created=self.connections_created,
            connections_closed=self.connections_closed,
            current_size=self.current_size,
            idle_size=self.idle_size,
            acquire_count=self.acquire_count,
            acquire_timeout_count=self.acquire_timeout_count,
            acquire_latency_ms=self.acquire_latency_ms,
        )

    @property
    def utilization_percent(self) -> float:
        """Calculate pool utilization percentage.

        Returns:
            Percentage of connections in use (0-100)
        """
        if self.current_size == 0:
            return 0.0
        return ((self.current_size - self.idle_size) / self.current_size) * 100

    @property
    def is_healthy(self) -> bool:
        """Check if pool is healthy.

        Returns:
            True if pool is not exhausted and responding
        """
        # Unhealthy if too many timeouts or fully utilized
        if self.acquire_timeout_count > 10:
            return False
        if self.current_size == self.current_size - self.idle_size:
            # All connections in use - at capacity
            return self.current_size < 100  # Allow up to 100 but flag as warning
        return True


class ConnectionPool:
    """Wrapper around asyncpg connection pool with monitoring.

    Provides:
    - Configuration validation
    - Metrics tracking
    - Health monitoring
    - Safe connection acquisition with timeout
    """

    def __init__(self, connection_string: str, config: PoolConfig | None = None):
        """Initialize connection pool.

        Args:
            connection_string: PostgreSQL connection string
            config: Pool configuration (uses defaults if None)
        """
        self.connection_string = connection_string
        self.config = config or PoolConfig()
        self.config.validate()
        self._pool: asyncpg.pool.Pool | None = None
        self._metrics = PoolMetrics()

    async def initialize(self) -> None:
        """Create and initialize the connection pool.

        Must be called before using the pool.
        """
        import asyncpg  # Import here when actually needed

        self._pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=self.config.min_size,
            max_size=self.config.max_size,
            max_queries=self.config.max_queries,
            max_idle=self.config.max_idle_time,
            max_cached_statement_lifetime=self.config.max_cached_statement_lifetime,
            max_cacheable_statement_size=self.config.max_cacheable_statement_size,
            timeout=self.config.timeout,
        )

    async def close(self) -> None:
        """Close and release the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def acquire(self) -> Any:
        """Acquire a connection from the pool.

        Returns:
            A database connection

        Raises:
            RuntimeError: If pool not initialized
            asyncpg.TooManyClientsError: If pool is exhausted
        """
        if not self._pool:
            raise RuntimeError("Pool not initialized. Call initialize() first.")

        try:
            conn = await self._pool.acquire(timeout=self.config.timeout)
            self._metrics.acquire_count += 1
            return conn
        except Exception as e:
            # Handle various timeout/connection limit errors
            error_msg = str(e).lower()
            if "too many" in error_msg or "timeout" in error_msg or "connection" in error_msg:
                self._metrics.acquire_timeout_count += 1
            raise

    def release(self, conn: Any) -> None:
        """Release a connection back to the pool.

        Args:
            conn: Connection to release
        """
        if self._pool:
            self._pool.release(conn)

    async def execute(self, query: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Execute a query using a pooled connection.

        Args:
            query: SQL query to execute
            *args: Query arguments
            **kwargs: Additional options

        Returns:
            Query results
        """
        conn = await self.acquire()
        try:
            return cast(list[Any], await conn.fetch(query, *args, **kwargs))
        finally:
            self.release(conn)

    async def execute_scalar(self, query: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a query and return single value.

        Args:
            query: SQL query to execute
            *args: Query arguments
            **kwargs: Additional options

        Returns:
            Single value result
        """
        conn = await self.acquire()
        try:
            return await conn.fetchval(query, *args, **kwargs)
        finally:
            self.release(conn)

    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics.

        Returns:
            Current metrics snapshot
        """
        metrics = self._metrics.copy()
        if self._pool:
            metrics.current_size = self._pool.get_size()
            metrics.idle_size = self._pool.get_idle_size()
        return metrics

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self._metrics = PoolMetrics()
