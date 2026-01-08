# Projection Demo

A minimal demo showing how to build a read model (projection) from events in Orchestrix.

## Scenario
You want to maintain a queryable view (read model) based on events.

## Example

```python
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
```

## Key Points
- Projections are just event handlers that update a read model.
- You can use any storage (dict, DB, etc.) for the read model.
