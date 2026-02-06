# E-Commerce Demo

Event-sourced order processing system with multi-aggregate saga, inventory management, and automatic compensation.

## What It Demonstrates
- **Multi-Aggregate Saga**: Order → Inventory → Payment coordinated in a single workflow
- **Compensation Flow**: If any step fails, all previous steps are automatically reversed
- **Event Sourcing**: Order lifecycle captured as immutable events
- **Validation**: Input validation with meaningful error messages

## Running

```bash
uv run python -m bases.orchestrix.ecommerce_demo.main
```

## Key Files
| File | Purpose |
|------|---------|
| `bases/orchestrix/ecommerce_demo/models.py` | Commands & Events (CreateOrder, ReserveInventory, ProcessPayment) |
| `bases/orchestrix/ecommerce_demo/aggregate.py` | OrderAggregate with state machine |
| `bases/orchestrix/ecommerce_demo/saga.py` | Order processing saga with compensation |
| `bases/orchestrix/ecommerce_demo/handlers.py` | Command handlers for all aggregate operations |
| `bases/orchestrix/ecommerce_demo/main.py` | Runnable entry point |

## Architecture
All domain logic lives in `bases/orchestrix/ecommerce_demo/`. This project assembly is a thin deployment wrapper following the Polylith pattern.
