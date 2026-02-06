
# Versioning Demo — Event Schema Evolution

Evolve event schemas over time without breaking existing event streams,
using upcasters and versioned events.

> **Source Code:**
> [`bases/orchestrix/versioning_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/versioning_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.versioning_demo.demo_versioning
```

## The Problem

Your event schema needs to evolve. Old events in the store use the old shape.
New code expects the new shape. Upcasters bridge the gap.

## Example — Adding Fields

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Event

# Version 1 — original shape
@dataclass(frozen=True, kw_only=True)
class UserCreatedV1(Event):
    user_id: str
    email: str

# Version 2 — extended with new fields (defaults for backward compat)
@dataclass(frozen=True, kw_only=True)
class UserCreatedV2(Event):
    user_id: str
    email: str
    username: str = ""
    created_at: str = ""
```

## Upcaster Pattern

Use `EventUpcaster` to transform old events on load:

```python
from orchestrix.core.eventsourcing.versioning import (
    EventUpcaster,
    UpcasterRegistry,
    VersionedEvent,
)

class UserCreatedV1ToV2(EventUpcaster):
    def __init__(self):
        super().__init__(source_version=1, target_version=2)

    async def upcast(self, event: Event) -> UserCreatedV2:
        return UserCreatedV2(
            user_id=event.user_id,
            email=event.email,
            username=event.email.split("@")[0],  # derive from email
            created_at="",  # unknown for old events
        )

# Register the upcaster
registry = UpcasterRegistry()
registry.register("UserCreated", UserCreatedV1ToV2())

# Upcast old events automatically
new_event = await registry.upcast(old_event, "UserCreated", target_version=2)
```

## Key Points

- **Always add new fields with defaults** — never remove or rename existing fields.
- **Use `EventUpcaster`** for transformations that can't be expressed as defaults.
- **`UpcasterRegistry`** chains upcasters: v1 → v2 → v3 automatically.
- **`VersionedEvent`** wraps an event with explicit version + type metadata.

## Related

- [Event Store Guide](../guide/event-store.md) — Persistence and replay
- [Best Practices](../guide/best-practices.md) — Schema evolution guidelines
