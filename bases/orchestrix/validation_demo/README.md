# Validation Demo

Input validation and guard clauses for domain events in Orchestrix.

## What It Demonstrates
- **Event Validation**: Checking field constraints before processing
- **ValidationError**: Structured error reporting with field-level details
- **Guard Clauses**: Email format, age range, username length checks

## Running

```bash
uv run python -m bases.orchestrix.validation_demo.demo_validation
```

## Key Concept

```python
def validate_user_registered(event: UserRegistered) -> None:
    if not is_valid_email(event.email):
        raise ValidationError("Invalid email format")
    if event.age < 18:
        raise ValidationError("Must be 18 or older")
```

Shows how to enforce business rules at the event boundary — reject invalid data before it enters the event store.
