# Banking Demo

Event-sourced banking system built with Orchestrix — account management, transfers, and saga-based compensation.

## What It Demonstrates
- **Event Sourcing**: Account state derived from immutable event streams
- **Aggregates**: `BankAccountAggregate` with deposit, withdraw, transfer logic
- **Sagas**: Multi-step transfer with automatic rollback on failure
- **Compensation**: If payment fails, previous steps are reversed

## Running

```bash
uv run python -m bases.orchestrix.banking_demo.main
```

## Key Files
| File | Purpose |
|------|---------|
| `bases/orchestrix/banking_demo/models.py` | Commands & Events (CreateAccount, Deposit, Transfer, etc.) |
| `bases/orchestrix/banking_demo/aggregate.py` | BankAccountAggregate with business rules |
| `bases/orchestrix/banking_demo/saga.py` | Transfer saga with compensation flow |
| `bases/orchestrix/banking_demo/handlers.py` | Command handlers wiring aggregate to bus |
| `bases/orchestrix/banking_demo/main.py` | Runnable entry point |

## Architecture
All domain logic lives in `bases/orchestrix/banking_demo/`. This project assembly (`projects/banking_demo/`) is a thin deployment wrapper following the Polylith pattern.