from dataclasses import dataclass
from orchestrix.core.messaging.message import Message
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrix.core.eventsourcing.event_store import EventStore
    from orchestrix.core.messaging.message_bus import MessageBus
    from orchestrix.core.common.module import Module


@dataclass(frozen=True, kw_only=True)
class RegisterUser(Message):
    """Command to register a new user (demo)."""

    user_id: str
    email: str
    password: str

    def __post_init__(self) -> None:
        """Validate email and password on creation."""
        if "@" not in self.email:
            raise ValueError("Invalid email")
        if len(self.password) < 8:
            raise ValueError("Password too short")


class ValidationModule(Module):
    """Demo module for user validation."""

    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register validation handler for RegisterUser command.

        Args:
            bus: The message bus.
            store: The event store (unused).
        """
        bus.subscribe(RegisterUser, lambda cmd: print(f"Validated: {cmd}"))
