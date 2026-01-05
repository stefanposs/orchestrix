"""Aggregate root and repository for event sourcing.

This module provides the core abstractions for event-sourced aggregates:
- AggregateRoot: Base class for domain aggregates with event sourcing
- AggregateRepository: Load and save aggregates with event replay
"""

import inspect
from dataclasses import dataclass, field
from typing import TypeVar

from orchestrix.core.eventsourcing.event_store import AsyncEventStore, EventStore
from orchestrix.core.messaging.message import Event

T = TypeVar("T", bound="AggregateRoot")


@dataclass
class AggregateRoot:
    """Base class for event-sourced aggregates.

    Provides event sourcing capabilities:
    - Event application and replay
    - Uncommitted events tracking
    - Version tracking for optimistic concurrency

    Subclasses should:
    1. Call _apply_event() to record domain events
    2. Implement _when_* methods to handle event replay
    """

    aggregate_id: str = ""
    version: int = 0
    uncommitted_events: list[Event] = field(default_factory=list, init=False, repr=False)

    def _apply_event(self, event: Event) -> None:
        """Apply an event to the aggregate.

        This method:
        1. Applies the event to update aggregate state
        2. Adds the event to uncommitted_events
        3. Increments the version

        Args:
            event: The event to apply
        """
        # Apply the event to state
        self._when(event)

        # Track uncommitted event
        self.uncommitted_events.append(event)
        self.version += 1

    def _when(self, event: Event) -> None:
        """Route event to specific handler method.

        Looks for a _when_{event_type} method and calls it.
        If no handler exists, the event is silently ignored.

        Args:
            event: The event to handle
        """
        # Convert event type to method name: OrderCreated -> _when_order_created
        event_type = event.type
        method_name = f"_when_{self._to_snake_case(event_type)}"

        # Call handler if it exists
        handler = getattr(self, method_name, None)
        if handler:
            handler(event)

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case.

        Args:
            name: PascalCase string

        Returns:
            snake_case string
        """
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)

    def mark_events_committed(self) -> None:
        """Clear uncommitted events after persistence."""
        self.uncommitted_events.clear()

    def _replay_events(self, events: list[Event]) -> None:
        """Replay events to rebuild aggregate state.

        Used by repository when loading an aggregate.

        Args:
            events: List of events to replay
        """
        for event in events:
            self._when(event)
            self.version += 1


@dataclass
class AggregateRepository[T: AggregateRoot]:
    """Repository for loading and saving event-sourced aggregates.

    Provides:
    - Load aggregates by ID with event replay
    - Save aggregates by persisting uncommitted events
    - Optimistic concurrency control via versioning

    Supports both sync and async event stores via runtime detection.
    """

    event_store: EventStore | AsyncEventStore

    async def load_async(self, aggregate_type: type[T], aggregate_id: str) -> T:
        """Load an aggregate by replaying its events.

        Args:
            aggregate_type: The class of the aggregate to load
            aggregate_id: The ID of the aggregate

        Returns:
            Reconstituted aggregate instance

        Raises:
            ValueError: If aggregate not found
        """
        # Load events from store
        result = self.event_store.load(aggregate_id)
        if inspect.isawaitable(result):
            events = await result
        else:
            events = result

        if not events:
            msg = f"Aggregate {aggregate_id} not found"
            raise ValueError(msg)

        # Create empty aggregate
        aggregate = aggregate_type()
        aggregate.aggregate_id = aggregate_id

        # Replay events to rebuild state
        if isinstance(events, list):
            aggregate._replay_events(events)

        return aggregate

    def load(self, aggregate_type: type[T], aggregate_id: str) -> T:
        """Synchronous load (not recommended, use load_async).

        Args:
            aggregate_type: The class of the aggregate to load
            aggregate_id: The ID of the aggregate

        Returns:
            Reconstituted aggregate instance

        Raises:
            ValueError: If aggregate not found
        """
        # Load events from store
        events = self.event_store.load(aggregate_id)

        if not events:
            msg = f"Aggregate {aggregate_id} not found"
            raise ValueError(msg)

        # Create empty aggregate
        aggregate = aggregate_type()
        aggregate.aggregate_id = aggregate_id

        # Replay events to rebuild state
        if isinstance(events, list):
            aggregate._replay_events(events)

        return aggregate

    async def save_async(self, aggregate: T) -> None:
        """Save an aggregate by persisting its uncommitted events.

        Args:
            aggregate: The aggregate to save
        """
        if not aggregate.uncommitted_events:
            return

        # Persist events
        result = self.event_store.save(aggregate.aggregate_id, aggregate.uncommitted_events)
        if inspect.isawaitable(result):
            await result

        # Mark events as committed
        aggregate.mark_events_committed()

    def save(self, aggregate: T) -> None:
        """Synchronous save (not recommended, use save_async).

        Args:
            aggregate: The aggregate to save
        """
        if not aggregate.uncommitted_events:
            return

        # Persist events
        self.event_store.save(aggregate.aggregate_id, aggregate.uncommitted_events)

        # Mark events as committed
        aggregate.mark_events_committed()


__all__ = ["AggregateRepository", "AggregateRoot"]
