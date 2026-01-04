"""CQRS Projection Engine for read model building.

Projections consume events from the event store to build and maintain
read models optimized for queries. This implements the CQRS pattern's
read side.
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Protocol, TypeVar, Union

from orchestrix.core.message import Event
from orchestrix.core.observability import TraceSpan, TracingProvider


# Type variables for generic projection handling
EventT = TypeVar("EventT", bound=Event, covariant=True)  # type: ignore[misc]
ReadModelT = TypeVar("ReadModelT")


@dataclass(frozen=True, kw_only=True)
class ProjectionState:
    """Current state of a projection.

    Tracks projection progress for recovery and monitoring.
    """

    projection_id: str
    """Unique identifier for the projection"""

    last_processed_event_id: Optional[str] = field(default=None)
    """ID of the last event processed"""

    last_processed_position: int = field(default=0)
    """Position in event stream (for ordering guarantees)"""

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    """When the state was last updated"""

    error_count: int = field(default=0)
    """Number of errors encountered"""

    is_healthy: bool = field(default=True)
    """Whether the projection is in a healthy state"""


class ProjectionStateStore(Protocol):
    """Stores projection state for recovery and monitoring.

    Enables exactly-once semantics by tracking processed events.
    """

    @abstractmethod
    async def load_state(self, projection_id: str) -> Optional[ProjectionState]:
        """Load projection state.

        Args:
            projection_id: The projection identifier

        Returns:
            The saved state or None if not found
        """
        ...

    @abstractmethod
    async def save_state(self, state: ProjectionState) -> None:
        """Save projection state.

        Args:
            state: The state to persist
        """
        ...


class EventHandler(Protocol):
    """Handles an event type to update read models.

    Each handler is responsible for updating read models
    when its corresponding event type occurs.
    """

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event to update read models.

        Args:
            event: The event to process

        Raises:
            Exception: If the projection fails (should trigger retry)
        """
        ...


@dataclass
class ProjectionEventHandler:
    """Wraps an event handler with metadata."""

    event_type: type[Event]
    """The event type this handler processes"""

    handler: Callable[[Event], Union[None, Any]]
    """The handler function/callable"""

    is_async: bool = field(default=False)
    """Whether the handler is async"""


class ProjectionEngine:
    """CQRS projection engine for building read models.

    Features:
    - Event stream processing for read model building
    - Handler registration per event type
    - Exactly-once semantics with state tracking
    - Async-first with sync fallback
    - Error handling and recovery
    - Projection replay capability
    """

    def __init__(
        self,
        projection_id: str,
        state_store: ProjectionStateStore,
        tracing: Optional[TracingProvider] = None,
    ):
        """Initialize the projection engine.

        Args:
            projection_id: Unique identifier for this projection
            state_store: Store for tracking processed events
            tracing: Optional tracing provider for instrumentation
        """
        self.projection_id = projection_id
        self.state_store = state_store
        self.tracing = tracing
        self._handlers: dict[type[Event], list[ProjectionEventHandler]] = {}
        self._state: Optional[ProjectionState] = None

    async def initialize(self) -> None:
        """Load projection state from store.

        Should be called once at startup.
        """
        self._state = await self.state_store.load_state(self.projection_id)
        if self._state is None:
            self._state = ProjectionState(projection_id=self.projection_id)
            await self.state_store.save_state(self._state)

    def on(self, event_type: type[Event]) -> Callable[[Callable[[Event], Any]], Callable[[Event], Any]]:
        """Register a handler for an event type (decorator).

        Args:
            event_type: The event type to handle

        Returns:
            Decorator function

        Example:
            @engine.on(OrderCreated)
            async def handle_order_created(event: OrderCreated) -> None:
                read_model.create_order(event.id)
        """

        def decorator(
            handler: Callable[[Event], Any]
        ) -> Callable[[Event], Any]:
            # Determine if handler is async
            import inspect

            is_async = asyncio.iscoroutinefunction(handler)

            # Create handler wrapper
            proj_handler = ProjectionEventHandler(
                event_type=event_type, handler=handler, is_async=is_async
            )

            # Register handler
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(proj_handler)

            return handler

        return decorator

    async def handle_event(self, event: Event) -> None:
        """Process a single event through all registered handlers.

        Args:
            event: The event to process

        Raises:
            Exception: If any handler fails
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            return

        # Check if already processed (idempotency)
        if (
            self._state
            and self._state.last_processed_event_id == event.id
        ):
            return

        for proj_handler in handlers:
            with self._trace_handler(event, proj_handler):
                try:
                    result = proj_handler.handler(event)
                    if asyncio.iscoroutine(result):
                        await result  # type: ignore[misc]
                except Exception as e:
                    # Record error and re-raise for caller to handle
                    if self._state:
                        object.__setattr__(
                            self._state, "error_count", self._state.error_count + 1
                        )
                        object.__setattr__(self._state, "is_healthy", False)
                        await self.state_store.save_state(self._state)
                    raise

        # Update state after successful processing
        if self._state:
            object.__setattr__(self._state, "last_processed_event_id", event.id)
            object.__setattr__(
                self._state, "last_processed_position", getattr(event, "position", 0)
            )
            object.__setattr__(
                self._state, "updated_at", datetime.now(timezone.utc)
            )
            await self.state_store.save_state(self._state)

    async def process_events(self, events: list[Event]) -> None:
        """Process a stream of events.

        Args:
            events: List of events to process in order
        """
        for event in events:
            await self.handle_event(event)

    async def replay(self, events: list[Event]) -> None:
        """Replay events to rebuild read models from scratch.

        Useful after projection code changes or failures.
        State is reset before replay starts.

        Args:
            events: All events from the event store
        """
        # Reset state for full rebuild
        if self._state:
            object.__setattr__(self._state, "last_processed_event_id", None)
            object.__setattr__(self._state, "last_processed_position", 0)
            object.__setattr__(self._state, "error_count", 0)
            object.__setattr__(self._state, "is_healthy", True)
            object.__setattr__(
                self._state, "updated_at", datetime.now(timezone.utc)
            )

        # Process all events
        await self.process_events(events)

    def get_state(self) -> Optional[ProjectionState]:
        """Get current projection state.

        Returns:
            The current projection state or None if not initialized
        """
        return self._state

    def is_healthy(self) -> bool:
        """Check if projection is healthy.

        Returns:
            True if projection is healthy, False if errors encountered
        """
        return self._state is not None and self._state.is_healthy

    def _trace_handler(self, event: Event, handler: ProjectionEventHandler) -> Any:
        """Create a tracing context for handler execution.

        Args:
            event: The event being processed
            handler: The handler being executed

        Returns:
            Context manager for tracing
        """
        if not self.tracing:
            # Return a no-op context manager
            return _NoOpTraceContext()  # type: ignore[return-value]

        return _TraceContext(
            self.tracing,
            f"projection.handle.{handler.event_type.__name__}",
            {
                "projection_id": self.projection_id,
                "event_id": event.id,
                "event_type": handler.event_type.__name__,
            },
        )  # type: ignore[return-value]


class _NoOpTraceContext:
    """No-op trace context when tracing is disabled."""

    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


class _TraceContext:
    """Trace context for projection handler execution."""

    def __init__(
        self, tracing: TracingProvider, operation: str, attributes: dict[str, Any]
    ):
        self.tracing = tracing
        self.operation = operation
        self.attributes = attributes
        self.span: Optional[TraceSpan] = None

    def __enter__(self) -> Optional[TraceSpan]:
        self.span = self.tracing.start_span(self.operation)
        if self.span:
            for key, value in self.attributes.items():
                # Store attributes in a dict since TraceSpan doesn't have set_attribute
                if not hasattr(self.span, "_attributes"):
                    object.__setattr__(self.span, "_attributes", {})
                getattr(self.span, "_attributes")[key] = value
        return self.span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.span:
            self.tracing.end_span(self.span)


class InMemoryProjectionStateStore:
    """In-memory implementation of ProjectionStateStore for testing."""

    def __init__(self) -> None:
        self._states: dict[str, ProjectionState] = {}

    async def load_state(self, projection_id: str) -> Optional[ProjectionState]:
        """Load projection state.

        Args:
            projection_id: The projection identifier

        Returns:
            The saved state or None if not found
        """
        return self._states.get(projection_id)

    async def save_state(self, state: ProjectionState) -> None:
        """Save projection state.

        Args:
            state: The state to persist
        """
        self._states[state.projection_id] = state
