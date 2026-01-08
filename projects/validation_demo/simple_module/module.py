from orchestrix import Module, MessageBus, EventStore
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class RegisterUser:
    user_id: str
    email: str
    password: str
    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError("Invalid email")
        if len(self.password) < 8:
            raise ValueError("Password too short")

class ValidationModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(RegisterUser, lambda cmd: print(f"Validated: {cmd}"))
