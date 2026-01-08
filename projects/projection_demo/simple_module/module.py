from dataclasses import dataclass
from orchestrix.core.common import Module
from orchestrix.core.eventsourcing import EventStore
from orchestrix.core.messaging import Message, MessageBus


@dataclass(frozen=True, kw_only=True)
class UserRegistered(Message):
    """Event emitted when a user registers (demo)."""

    user_id: str
    email: str


class ProjectionModule(Module):
    """Demo module for projections."""

    def __init__(self):
        """Initializes the projection module and its read model."""
        self.user_emails = {}

    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register event handler for UserRegistered events.

        Args:
            bus: The message bus.
            store: The event store (unused).
        """

        def project(event: UserRegistered) -> None:
            """Projects the UserRegistered event into the read model."""
            self.user_emails[event.user_id] = event.email

        bus.subscribe(UserRegistered, project)
