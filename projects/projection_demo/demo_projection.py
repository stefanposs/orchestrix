from dataclasses import dataclass
from orchestrix.core.messaging import Event
from orchestrix.infrastructure.memory import InMemoryMessageBus


@dataclass(frozen=True, kw_only=True)
class UserRegistered(Event):
    """Event emitted when a user registers."""

    user_id: str
    email: str


# Simple projection (read model)
user_emails = {}


def project_user_registered(event: UserRegistered) -> None:
    """Projects the UserRegistered event into the user_emails read model."""
    user_emails[event.user_id] = event.email


bus = InMemoryMessageBus()
bus.subscribe(UserRegistered, project_user_registered)

bus.publish(UserRegistered(user_id="u1", email="a@example.com"))
print(user_emails)  # {"u1": "a@example.com"}
