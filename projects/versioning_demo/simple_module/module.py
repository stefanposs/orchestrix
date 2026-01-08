from orchestrix import Module, MessageBus, EventStore
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class UserCreatedV1:
    user_id: str
    email: str

@dataclass(frozen=True, kw_only=True)
class UserCreatedV2:
    user_id: str
    email: str
    username: str = ""
    created_at: str = ""

class VersioningModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(UserCreatedV1, lambda e: print(f"V1: {e}"))
        bus.subscribe(UserCreatedV2, lambda e: print(f"V2: {e}"))
