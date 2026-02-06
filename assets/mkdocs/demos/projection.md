
# Projection Demo — Building Read Models

Build queryable read models (projections) from event streams using the CQRS pattern.

> **Source Code:**
> [`bases/orchestrix/projection_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/projection_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.projection_demo.demo_projection
```

## Example

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Event
from orchestrix.infrastructure.memory.store import InMemoryEventStore

@dataclass(frozen=True, kw_only=True)
class AccountCreated(Event):
    account_id: str
    owner: str

@dataclass(frozen=True, kw_only=True)
class MoneyDeposited(Event):
    account_id: str
    amount: float

# Simple projection — a dict-based read model
class AccountProjection:
    def __init__(self):
        self.balances: dict[str, float] = {}
        self.owners: dict[str, str] = {}

    def apply_created(self, event: AccountCreated):
        self.balances[event.account_id] = 0.0
        self.owners[event.account_id] = event.owner

    def apply_deposited(self, event: MoneyDeposited):
        self.balances[event.account_id] += event.amount

    def get_balance(self, account_id: str) -> float:
        return self.balances.get(account_id, 0.0)
```

## Orchestrix Projection Engine

For production use, Orchestrix provides a `ProjectionEngine` with state tracking:

```python
from orchestrix.core.eventsourcing.projection import (
    ProjectionEngine,
    InMemoryProjectionStateStore,
)

state_store = InMemoryProjectionStateStore()
engine = ProjectionEngine(projection_id="account-balance", state_store=state_store)

@engine.on(AccountCreated)
async def on_created(event: AccountCreated):
    # Update your read model
    ...

@engine.on(MoneyDeposited)
async def on_deposited(event: MoneyDeposited):
    # Update your read model
    ...

# Process a batch of events
await engine.process_events(events)
```

## Key Points

- Projections are event handlers that build denormalized query models.
- Use any storage backend (dict, database, cache) for the read model.
- `ProjectionEngine` tracks processing state (`ProjectionState`) for reliability.
- Supports replay: `await engine.replay(events)` rebuilds from scratch.

## Related

- [Event Store Guide](../guide/event-store.md) — Persist and replay events
- [Banking Demo](banking.md) — Event-sourced aggregates
