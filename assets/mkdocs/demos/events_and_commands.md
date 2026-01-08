# Events & Commands Demo

A minimal demo showing the difference between commands and events in Orchestrix.

## Scenario
You want to understand the core message types: Command (intention) and Event (fact).

## Example

```python
from dataclasses import dataclass
from orchestrix import Command, Event

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    amount: float

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    amount: float
```

## Key Points
- Commands express what should happen (intention).
- Events express what has happened (fact).
- Commands are handled by one handler, events by zero or more.
