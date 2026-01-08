# Validation Demo

A minimal demo showing how to validate commands and events in Orchestrix.

## Scenario
You want to ensure only valid data is processed by your aggregates and handlers.

## Example

```python
from dataclasses import dataclass
from orchestrix import Command

@dataclass(frozen=True, kw_only=True)
class RegisterUser(Command):
    user_id: str
    email: str
    password: str
    
    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError("Invalid email")
        if len(self.password) < 8:
            raise ValueError("Password too short")
```

## Key Points
- Use __post_init__ in dataclasses for validation.
- Raise exceptions to reject invalid commands before they reach handlers.
