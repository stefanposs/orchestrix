# Projection Demo

Read model projections from event streams — the CQRS query side of Orchestrix.

## What It Demonstrates
- **Projection Engine**: Building denormalized read models from events
- **Account Projection**: Maintaining balance and owner state across multiple event types
- **Event Replay**: Reconstructing current state by replaying `AccountCreated`, `MoneyDeposited`, `MoneyWithdrawn`

## Running

```bash
uv run python -m bases.orchestrix.projection_demo.demo_projection
```

## Key Concept

```python
class AccountProjection:
    """Builds queryable state from an event stream."""
    balances: dict[str, float]
    owners: dict[str, str]

    def apply(self, event: Event) -> None:
        match event:
            case AccountCreated(): ...
            case MoneyDeposited(): ...
            case MoneyWithdrawn(): ...
```

Ideal for understanding how CQRS separates write (event store) from read (projections) models.
