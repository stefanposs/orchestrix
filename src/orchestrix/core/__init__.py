"""Core abstractions for event sourcing and CQRS.

This module provides the essential building blocks for event-sourced applications:
- AggregateRoot: Base class for domain aggregates
- AggregateRepository: Load and save aggregates with event replay
- Event: CloudEvents-compatible events
- MessageBus: Publish/subscribe messaging
- Observability: Metrics, tracing, and monitoring hooks
"""

from orchestrix.core.aggregate import AggregateRepository, AggregateRoot
from orchestrix.core.message import Event
from orchestrix.core.messaging import MessageBus
from orchestrix.core.observability import (
    MetricType,
    MetricValue,
    MetricsProvider,
    NoOpMetricsProvider,
    NoOpTracingProvider,
    ObservabilityHooks,
    TraceSpan,
    TracingProvider,
    get_observability,
    init_observability,
    set_observability,
)

__all__ = [
    "AggregateRepository",
    "AggregateRoot",
    "Event",
    "MessageBus",
    "MetricType",
    "MetricValue",
    "MetricsProvider",
    "NoOpMetricsProvider",
    "NoOpTracingProvider",
    "ObservabilityHooks",
    "TraceSpan",
    "TracingProvider",
    "get_observability",
    "init_observability",
    "set_observability",
]

