"""Orchestrix Infrastructure - Message Bus and Event Store implementations."""

from orchestrix.infrastructure.connection_pool import (
    ConnectionPool,
    PoolConfig,
    PoolMetrics,
)
from orchestrix.infrastructure.inmemory_bus import InMemoryMessageBus
from orchestrix.infrastructure.inmemory_store import InMemoryEventStore
from orchestrix.infrastructure.prometheus_metrics import (
    MetricConfig,
    MetricOperationType,
    PrometheusMetrics,
)
from orchestrix.infrastructure.tracing import (
    JaegerTracer,
    TracingConfig,
    get_tracer,
    init_tracing,
)

# Optional imports with graceful fallback
try:
    from orchestrix.infrastructure.postgres_store import PostgreSQLEventStore
except ImportError:
    PostgreSQLEventStore = None  # type: ignore

try:
    from orchestrix.infrastructure.eventsourcingdb_store import EventSourcingDBStore
except ImportError:
    EventSourcingDBStore = None  # type: ignore

__all__ = [
    "ConnectionPool",
    "EventSourcingDBStore",
    "InMemoryEventStore",
    "InMemoryMessageBus",
    "JaegerTracer",
    "MetricConfig",
    "MetricOperationType",
    "PoolConfig",
    "PoolMetrics",
    "PostgreSQLEventStore",
    "PrometheusMetrics",
    "TracingConfig",
    "get_tracer",
    "init_tracing",
]
