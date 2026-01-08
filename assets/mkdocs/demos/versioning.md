# Versioning Demo

A minimal demo showing how to handle event and schema versioning in Orchestrix.

## Scenario
Suppose you want to evolve your event schema without breaking old events. This demo shows how to add a new field to an event and keep everything compatible.

## Example

```python
from dataclasses import dataclass
from orchestrix import Event

# Version 1
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str

# Version 2 (backward compatible)
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str
    username: str = ""  # Default for old events
    created_at: str = ""
```

## Key Points
- Always add new fields with defaults for backward compatibility.
- Never remove or rename fields in existing events.
- Use versioned event handlers if you need to support multiple shapes.
