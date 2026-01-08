from orchestrix import InMemoryMessageBus, Event
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class UserRegistered(Event):
    user_id: str
    email: str

# Simple projection (read model)
user_emails = {}

def project_user_registered(event: UserRegistered):
    user_emails[event.user_id] = event.email

bus = InMemoryMessageBus()
bus.subscribe(UserRegistered, project_user_registered)

bus.publish(UserRegistered(user_id="u1", email="a@example.com"))
print(user_emails)  # {"u1": "a@example.com"}
