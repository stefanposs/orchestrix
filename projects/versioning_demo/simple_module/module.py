from dataclasses import dataclass
from orchestrix.core.messaging.message import Message
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrix.core.eventsourcing.event_store import EventStore
    from orchestrix.core.messaging.message_bus import MessageBus
    from orchestrix.core.common.module import Module


@dataclass(frozen=True, kw_only=True)
class UserCreatedV1(Message):
    """Version 1 of the UserCreated event (demo)."""

    user_id: str
    email: str


@dataclass(frozen=True, kw_only=True)
class UserCreatedV2(Message):
    """Version 2 of the UserCreated event (demo)."""

    user_id: str
    email: str
    username: str = ""
    created_at: str = ""


class VersioningModule(Module):
    """Demo module for event versioning."""

    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register handlers for both event versions.

        Args:
            bus: The message bus.
            store: The event store (unused).
        """
        bus.subscribe(UserCreatedV1, lambda e: print(f"V1: {e}"))
        bus.subscribe(UserCreatedV2, lambda e: print(f"V2: {e}"))
