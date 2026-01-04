"""Core abstractions for event sourcing and CQRS.

This module provides the essential building blocks for event-sourced applications:
- AggregateRoot: Base class for domain aggregates
- AggregateRepository: Load and save aggregates with event replay
- Event: CloudEvents-compatible events
- MessageBus: Publish/subscribe messaging
- ProjectionEngine: CQRS read model building
- Saga: Distributed transaction orchestration
- Observability: Metrics, tracing, and monitoring hooks
"""

from orchestrix.core.aggregate import AggregateRepository, AggregateRoot
from orchestrix.core.exceptions import ConcurrencyError, HandlerError, OrchestrixError
from orchestrix.core.message import Event
from orchestrix.core.messaging import MessageBus
from orchestrix.core.observability import (
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
from orchestrix.core.projection import (
    EventHandler,
    InMemoryProjectionStateStore,
    ProjectionEngine,
    ProjectionEventHandler,
    ProjectionState,
    ProjectionStateStore,
)
from orchestrix.core.saga import (
    InMemorySagaStateStore,
    Saga,
    SagaState,
    SagaStateStore,
    SagaStatus,
    SagaStep,
    SagaStepStatus,
)
from orchestrix.core.versioning import (
    EventUpcaster,
    EventUpcast,
    UpcasterException,
    UpcasterRegistry,
    VersionedEvent,
)

__all__ = [
    "AggregateRepository",
    "AggregateRoot",
    "ConcurrencyError",
    "Event",
    "EventHandler",
    "EventUpcaster",
    "EventUpcast",
    "HandlerError",
    "InMemoryProjectionStateStore",
    "InMemorySagaStateStore",
    "MessageBus",
    "MetricType",
    "MetricValue",
    "MetricsProvider",
    "NoOpMetricsProvider",
    "NoOpTracingProvider",
    "ObservabilityHooks",
    "OrchestrixError",
    "ProjectionEngine",
    "ProjectionEventHandler",
    "ProjectionState",
    "ProjectionStateStore",
    "Saga",
    "SagaState",
    "SagaStateStore",
    "SagaStatus",
    "SagaStep",
    "SagaStepStatus",
    "TraceSpan",
    "TracingProvider",
    "UpcasterException",
    "UpcasterRegistry",
    "VersionedEvent",
    "get_observability",
    "init_observability",
    "set_observability",
]

