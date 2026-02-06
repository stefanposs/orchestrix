
# Events & Commands Demo

Minimal demo showing the core message types: **Command** (intention) and **Event** (fact).

> **Source Code:**
> [`bases/orchestrix/events_and_commands_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/events_and_commands_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.events_and_commands_demo.demo_events_and_commands
```

## Example

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Command, Event

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

- **Commands** express what *should* happen (intention). Imperative naming: `CreateOrder`.
- **Events** express what *has* happened (fact). Past-tense naming: `OrderCreated`.
- Commands are handled by **one** handler; events by **zero or more**.
- Both inherit from `Message` which is **CloudEvents-compatible** (auto-generated `id`, `timestamp`, `type`, etc.).

## Module Pattern

The demo also includes `simple_module/module.py` showing the `Module` protocol:

```python
from orchestrix.core.common.module import Module

class EventsAndCommandsModule:
    def register(self, bus, store):
        bus.subscribe(CreateOrder, self._handle_create_order)
        # ...
```

## Related

- [Core Concepts](../getting-started/concepts.md) — Message, Command, Event in depth
- [Commands & Events Guide](../guide/commands-events.md) — Design guidelines
