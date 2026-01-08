from dataclasses import dataclass
from orchestrix import Event

# Version 1
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str

# Version 2 (backward compatible)
@dataclass(frozen=True, kw_only=True)
class UserCreatedV2(Event):
    user_id: str
    email: str
    username: str = ""  # Default for old events
    created_at: str = ""

# Usage: handle both event shapes in your handler
