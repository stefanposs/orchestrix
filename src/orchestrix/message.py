"""Core message abstractions for Orchestrix.

Messages are immutable, CloudEvents-compatible data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)  # type: ignore[call-overload]
class Message:
    """Base class for all messages in Orchestrix.

    CloudEvents-compatible immutable message with metadata.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = field(default="")
    source: str = field(default="orchestrix")
    timestamp: datetime = field(default_factory=datetime.utcnow)

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
