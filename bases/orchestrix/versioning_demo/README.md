# Versioning Demo

Event schema evolution using version-aware handlers in Orchestrix.

## What It Demonstrates
- **Event Versioning**: `UserCreatedV1` (basic) → `UserCreatedV2` (extended with username + timestamp)
- **Multi-Version Handlers**: Separate handlers for each schema version on the same bus
- **Backward Compatibility**: Old and new event versions coexist without breaking consumers

## Running

```bash
uv run python -m bases.orchestrix.versioning_demo.demo_versioning
```

## Key Concept

```python
@dataclass(frozen=True)
class UserCreatedV1(Event):
    user_id: str
    email: str

@dataclass(frozen=True)
class UserCreatedV2(Event):
    user_id: str
    email: str
    username: str
    created_at: datetime
```

Essential for production systems where event schemas evolve over time — Orchestrix upcasters handle the migration transparently.
