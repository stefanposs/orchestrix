"""Core message abstractions for Orchestrix.

Messages are immutable, CloudEvents-compatible data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)  # type: ignore[call-overload]
class Message:
    """Base class for all messages in Orchestrix.

    CloudEvents-compatible immutable message with metadata.

    CloudEvents v1.0 Specification:
    - id: Unique identifier for the event
    - type: Event type (defaults to class name)
    - source: Context in which the event occurred
    - timestamp: When the event occurred (ISO 8601)
    - subject: The subject of the event in context of the source (optional)
    - datacontenttype: Content type of the data (optional)
    - dataschema: Schema that data adheres to (optional)
    - correlation_id: For tracing related events across services (extension)
    - causation_id: ID of the message that caused this message (extension)
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = field(default="")
    source: str = field(default="orchestrix")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subject: Optional[str] = field(default=None)
    datacontenttype: Optional[str] = field(default=None)
    dataschema: Optional[str] = field(default=None)
    correlation_id: Optional[str] = field(default=None)
    causation_id: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        """Set type from class name if not provided."""
        if not self.type:
            object.__setattr__(self, "type", self.__class__.__name__)


@dataclass(frozen=True)
class Command(Message):
    """A command represents an intent to perform an action.

    Commands are handled by CommandHandlers and may result in Events.
    """


@dataclass(frozen=True)
class Event(Message):
    """An event represents a fact that has occurred.

    Events are immutable records of state changes.
    """
