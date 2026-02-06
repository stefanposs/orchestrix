
# Commands & Events

Design guidelines for messages in Orchestrix.

## Message Hierarchy

```
Message (base — CloudEvents-compatible)
├── Command  (intention to change state)
└── Event    (fact that occurred)
```

All messages are `@dataclass(frozen=True)` with auto-generated `id`, `type`,
`source`, `timestamp`, `correlation_id`, `causation_id`, `trace_id`.

## Defining Commands

Commands express **what should happen**. Use imperative naming.

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Command

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_name: str
    total_amount: float
```

Commands may be rejected (validation, business rules). Each command is
handled by **exactly one** handler.

## Defining Events

Events express **what has happened**. Use past-tense naming.

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Event

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str
    total_amount: float
```

Events are immutable facts. They can be handled by **zero or more** handlers
(projections, notifications, side effects).

## CloudEvents Fields

Every `Message` includes these fields (set automatically):

| Field | Type | Description |
|---|---|---|
| `id` | `str` | UUID v4 |
| `specversion` | `str` | `"1.0"` |
| `type` | `str` | Class name (auto-derived) |
| `source` | `str` | `"orchestrix"` |
| `timestamp` | `datetime` | UTC now |
| `subject` | `str \| None` | Optional subject |
| `data` | `Any` | Optional payload |
| `correlation_id` | `str \| None` | Links related messages |
| `causation_id` | `str \| None` | ID of the causing message |
| `trace_id` | `str \| None` | Distributed trace ID |

## Validation

Use `__post_init__` for input validation:

```python
from orchestrix.core.common.validation import validate_not_empty, validate_positive

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    amount: float

    def __post_init__(self):
        super().__post_init__()  # sets type field
        validate_not_empty(self.order_id, "order_id")
        validate_positive(self.amount, "amount")
```

## Naming Conventions

| Type | Convention | Examples |
|---|---|---|
| Command | Imperative verb + noun | `CreateOrder`, `SuspendAccount`, `PublishBatch` |
| Event | Noun + past participle | `OrderCreated`, `AccountSuspended`, `BatchPublished` |

## Best Practices

1. **Keep messages small** — only include data the handler needs
2. **Use frozen dataclasses** — messages must be immutable
3. **Add `kw_only=True`** — prevents positional constructor errors
4. **Prefer primitive types** — strings, numbers, booleans for serializability
5. **Never put behavior in messages** — messages are pure data
6. **Version events carefully** — see [Versioning Demo](../demos/versioning.md)
