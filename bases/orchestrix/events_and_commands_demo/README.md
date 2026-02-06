# Events & Commands Demo

Minimal demonstration of the core command/event distinction in Orchestrix.

## What It Demonstrates
- **Commands** as frozen dataclasses representing intentions (requests to change state)
- **Events** as frozen dataclasses representing facts (state changes that occurred)
- **Simple Module** with handler registration and message bus wiring

## Running

```bash
uv run python -m bases.orchestrix.events_and_commands_demo.demo_events_and_commands
```

## Key Concepts

```python
# Command = intention (imperative: "Create this order")
@dataclass(frozen=True)
class CreateOrder(Command):
    order_id: str
    customer_name: str

# Event = fact (past tense: "Order was created")
@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str
```

This is the simplest Orchestrix demo — start here if you are new to event-driven design.
