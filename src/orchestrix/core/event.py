"""Event wrapper for CloudEvents-compatible events.

This module provides a convenient Event class that wraps CloudEvents
with additional metadata for event sourcing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from orchestrix.core.message import Event as BaseEvent


@dataclass
class Event:
    """Event wrapper with metadata for event sourcing.

    Provides a higher-level interface over the base CloudEvents-compatible
    Event class, adding convenience methods for aggregate-based event sourcing.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    source: str = ""
    subject: str = ""
    data: object = None
    time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    datacontenttype: str = "application/json"
    specversion: str = "1.0"

    @classmethod
    def from_aggregate(
        cls,
        aggregate: object,
        event_type: str,
        data: object,
        source: str | None = None,
    ) -> "Event":
        """Create an event from an aggregate.

        Args:
            aggregate: The aggregate that produced the event
            event_type: The type/name of the event
            data: The event payload
            source: Optional source URI (defaults to aggregate type)

        Returns:
            Event instance
        """
        aggregate_type = type(aggregate).__name__
        aggregate_id = getattr(aggregate, "aggregate_id", None) or getattr(
            aggregate, "id", ""
        )

        return cls(
            type=event_type,
            source=source or f"/{aggregate_type.lower()}",
            subject=aggregate_id,
            data=data,
        )

    def to_base_event(self) -> BaseEvent:
        """Convert to base Event for message bus.

        Returns:
            BaseEvent instance compatible with message bus
        """
        return BaseEvent(
            id=self.id,
            type=self.type,
            source=self.source,
            subject=self.subject,
            data=self.data,
            time=self.time,
            datacontenttype=self.datacontenttype,
            specversion=self.specversion,
        )

    @classmethod
    def from_base_event(cls, base_event: BaseEvent) -> "Event":
        """Create from base Event.

        Args:
            base_event: Base Event instance

        Returns:
            Event instance
        """
        return cls(
            id=base_event.id,
            type=base_event.type,
            source=base_event.source,
            subject=base_event.subject,
            data=base_event.data,
            time=base_event.time,
            datacontenttype=base_event.datacontenttype,
            specversion=base_event.specversion,
        )


__all__ = ["Event"]
