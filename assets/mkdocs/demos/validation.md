
# Validation Demo — Input Validation & Guard Clauses

Validate commands and events before processing, using Orchestrix's built-in
validation utilities.

> **Source Code:**
> [`bases/orchestrix/validation_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/validation_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.validation_demo.demo_validation
```

## Built-in Validators

Orchestrix provides ready-made validation functions in `orchestrix.core.common.validation`:

```python
from orchestrix.core.common.validation import (
    ValidationError,
    validate_not_empty,
    validate_positive,
    validate_non_negative,
    validate_min_length,
    validate_max_length,
    validate_in_range,
    validate_one_of,
)

# Examples
validate_not_empty(email, "email")            # raises ValidationError if empty
validate_positive(amount, "amount")           # raises if ≤ 0
validate_min_length(username, 3, "username")  # raises if too short
validate_in_range(age, 18, 120, "age")        # raises if out of range
validate_one_of(status, ["active", "suspended"], "status")
```

## Dataclass Validation Pattern

Use `__post_init__` for command-level validation:

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Command
from orchestrix.core.common.validation import validate_not_empty, validate_positive

@dataclass(frozen=True, kw_only=True)
class RegisterUser(Command):
    email: str
    age: int
    username: str

    def __post_init__(self):
        validate_not_empty(self.email, "email")
        validate_positive(self.age, "age")
        validate_min_length(self.username, 3, "username")
```

## Key Points

- Validate in `__post_init__` so invalid messages cannot be constructed.
- `ValidationError` carries `message`, `field`, and `value` for error reporting.
- Keep validation in the message layer, business rules in the aggregate.

## Related

- [Commands & Events Guide](../guide/commands-events.md) — Message design
- [Best Practices](../guide/best-practices.md) — Error handling patterns
