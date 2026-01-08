# Tracing Demo

A minimal demo showing how to trace event flow in Orchestrix.

## Scenario
You want to track the flow of commands and events for debugging or observability.

## Example

```python
from orchestrix import InMemoryMessageBus, Command, Event
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class MyCommand(Command):
    value: int

@dataclass(frozen=True, kw_only=True)
class MyEvent(Event):
    value: int

bus = InMemoryMessageBus()

# Simple tracing handler
bus.subscribe(MyCommand, lambda cmd: print(f"TRACE: Command {cmd}"))
bus.subscribe(MyEvent, lambda evt: print(f"TRACE: Event {evt}"))

bus.publish(MyCommand(value=42))
```

## Key Points
- Use bus.subscribe to add tracing/logging handlers.
- You can integrate with OpenTelemetry or other tracing tools for production.
