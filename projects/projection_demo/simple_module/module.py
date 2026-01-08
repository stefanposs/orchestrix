from orchestrix import Module, MessageBus, EventStore
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class UserRegistered:
    user_id: str
    email: str

class ProjectionModule(Module):
    def __init__(self):
        self.user_emails = {}
    def register(self, bus: MessageBus, store: EventStore) -> None:
        def project(event: UserRegistered):
            self.user_emails[event.user_id] = event.email
        bus.subscribe(UserRegistered, project)
