"""Event versioning and schema evolution via upcasting.

This module provides mechanisms for handling event schema evolution in event sourcing systems.
When domain events need to change structure over time, upcasters transform old event versions
into new versions, enabling seamless schema migration without breaking existing event stores.

Key concepts:
- EventUpcast: Protocol for transforming events from one version to another
- EventUpcaster: Generic implementation for version mapping chains
- VersionedEvent: Event with explicit version tracking
- UpcasterRegistry: Central registry for version transformations

Example:
    # Define old and new event versions
    @dataclass(frozen=True)
    class OrderCreatedV1(Event):
        order_id: str
        customer_id: str
        total: float

    @dataclass(frozen=True)
    class OrderCreatedV2(Event):
        order_id: str
        customer_id: str
        total: float
        currency: str  # New field

    # Define upcast transformation
    class OrderCreatedUpcaster(EventUpcaster[OrderCreatedV1, OrderCreatedV2]):
        async def upcast(self, event: OrderCreatedV1) -> OrderCreatedV2:
            return OrderCreatedV2(
                order_id=event.order_id,
                customer_id=event.customer_id,
                total=event.total,
                currency="USD"  # Default currency for legacy events
            )

    # Register and use
    registry = UpcasterRegistry()
    registry.register(OrderCreatedUpcaster())

    # Automatic upcasting on read
    upgraded_event = await registry.upcast(legacy_event, target_version=2)
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol, TypeVar

from orchestrix.core.messaging.message import Event

# Event type variables for generic upcasting
SourceEvent = TypeVar("SourceEvent", bound=Event)
TargetEvent = TypeVar("TargetEvent", bound=Event)


class EventUpcast(Protocol):
    """Protocol for transforming events between versions.

    Implementations define how to migrate from one event schema version to another.
    This supports gradual schema evolution in event-sourced systems.
    """

    async def upcast(self, event: Event) -> Event:
        """Transform event from source version to target version.

        Args:
            event: Event in source schema version

        Returns:
            Event transformed to target schema version

        Raises:
            UpcasterException: If transformation fails or is invalid
        """


class EventUpcaster[SourceEvent, TargetEvent]:
    """Base class for event version transformations.

    Provides common functionality for upcasting events between versions,
    including validation, context passing, and error handling.

    Type parameters:
        SourceEvent: Original event type/version
        TargetEvent: Target event type/version
    """

    source_version: int
    target_version: int

    def __init__(self, source_version: int, target_version: int) -> None:
        """Initialize upcaster with version information.

        Args:
            source_version: Version number of source event schema
            target_version: Version number of target event schema
        """
        if not isinstance(source_version, int) or source_version < 1:
            raise ValueError("source_version must be positive integer")
        if not isinstance(target_version, int) or target_version < 1:
            raise ValueError("target_version must be positive integer")
        if source_version >= target_version:
            raise ValueError("target_version must be greater than source_version")

        self.source_version = source_version
        self.target_version = target_version

    @abstractmethod
    async def upcast(self, event: Event) -> TargetEvent:
        """Transform event to next version.

        Subclasses must implement specific migration logic.

        Args:
            event: Event to transform

        Returns:
            Transformed event

        Raises:
            UpcasterException: If transformation fails
        """

    async def can_upcast(self, event: Event) -> bool:
        """Check if this upcaster can process the event.

        Default implementation checks event type and version.
        Override for custom logic.

        Args:
            event: Event to check

        Returns:
            True if this upcaster can process the event
        """
        return hasattr(event, "version") and event.version == self.source_version


@dataclass(frozen=True)
class VersionedEvent:
    """Wrapper for events with explicit version tracking.

    Enables versioned event storage and retrieval with upcasting support.
    """

    event: Event
    version: int
    event_type: str

    def __post_init__(self) -> None:
        """Validate version information."""
        if self.version < 1:
            raise ValueError("version must be positive integer")
        if not self.event_type or not isinstance(self.event_type, str):
            raise ValueError("event_type must be non-empty string")


class UpcasterRegistry:
    """Central registry for event version transformations.

    Manages upcast chains and applies them automatically when reading events.
    Supports multi-step upcasting (v1 -> v2 -> v3) via chaining.

    Example:
        registry = UpcasterRegistry()
        registry.register(OrderCreatedUpcaster())
        registry.register(OrderUpdatedUpcaster())

        # Automatically chains upcasts
        upgraded = await registry.upcast(old_event, target_version=3)
    """

    def __init__(self) -> None:
        """Initialize empty upcaster registry."""
        self._upcasters: dict[tuple[str, int, int], EventUpcast] = {}

    def register(self, event_type: str, upcaster: EventUpcast) -> None:
        """Register an upcaster for event type and versions.

        Args:
            event_type: Type name of event being upcasted
            upcaster: Upcaster instance implementing transformation

        Raises:
            ValueError: If upcaster already registered for this event/versions
        """
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type must be non-empty string")

        # Get source and target versions from upcaster
        if not isinstance(upcaster, EventUpcaster):
            raise ValueError("upcaster must be instance of EventUpcaster")

        key: tuple[str, int, int] = (event_type, upcaster.source_version, upcaster.target_version)
        if key in self._upcasters:
            raise ValueError(
                f"Upcaster already registered for {event_type} "
                f"v{upcaster.source_version}->v{upcaster.target_version}"
            )

        self._upcasters[key] = upcaster

    def get_upcaster(
        self, event_type: str, source_version: int, target_version: int
    ) -> EventUpcast | None:
        """Get single-step upcaster between versions.

        Args:
            event_type: Type name of event
            source_version: Version event is currently in
            target_version: Desired target version

        Returns:
            Upcaster if registered, None otherwise
        """
        return self._upcasters.get((event_type, source_version, target_version))

    async def upcast(self, event: Event, event_type: str, target_version: int) -> Event:
        """Upcast event through chain to reach target version.

        Automatically finds and applies intermediate upcasters as needed.

        Args:
            event: Event to upcast
            event_type: Type name of event
            target_version: Desired target version

        Returns:
            Upcasted event at target version

        Raises:
            UpcasterException: If upcasting chain is incomplete or fails
        """
        if not hasattr(event, "version"):
            raise UpcasterException(f"Event {event} missing version attribute for upcasting")

        current_version: int = event.version

        if current_version == target_version:
            return event

        if current_version > target_version:
            raise UpcasterException(f"Cannot downcast from v{current_version} to v{target_version}")

        # Chain upcasts from current to target version
        result = event
        current = current_version

        while current < target_version:
            next_version = current + 1
            upcaster = self.get_upcaster(event_type, current, next_version)

            if not upcaster:
                raise UpcasterException(
                    f"No upcaster found for {event_type} v{current}->{next_version}"
                )

            try:
                result = await upcaster.upcast(result)
                # Update version tracking
                if hasattr(result, "version"):
                    object.__setattr__(result, "version", next_version)
            except Exception as exc:
                raise UpcasterException(
                    f"Upcasting {event_type} v{current}->{next_version} failed: {exc}"
                ) from exc

            current = next_version

        return result

    def get_chain_info(self, event_type: str) -> list[tuple[int, int]]:
        """Get available upcasting paths for event type.

        Returns list of (source_version, target_version) tuples
        showing which upgrade paths are registered.

        Args:
            event_type: Type name to check

        Returns:
            List of available version transitions
        """
        return [(src, tgt) for (etype, src, tgt) in self._upcasters if etype == event_type]


class UpcasterException(Exception):
    """Raised when event upcasting fails.

    Indicates schema migration error, missing upcaster, or transformation failure.
    """
