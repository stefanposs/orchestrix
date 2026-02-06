
# Demos

Production-ready demos showcasing real-world event-sourcing patterns.
Each demo is self-contained and runnable.

## Practical Demos

### [Banking](banking.md)
Account management with event sourcing, transfer saga, and compensation flows.

### [E-Commerce](ecommerce.md)
Order processing with multi-aggregate saga, payment, inventory, and automatic rollback.

### [Lakehouse Platform](lakehouse.md)
Self-service data platform with GDPR compliance, batch lifecycle, data contracts,
quality gates, and a FastAPI REST API with real-time SSE streaming.

### [Notifications](notifications.md)
Resilient notification system with retry policies, exponential backoff,
and dead letter queue.

### [Projections](projection.md)
Read-model construction from event streams — CQRS pattern with denormalized query models.

### Web GUI
Interactive Dash dashboard for exploring events, commands, and aggregate state.

```bash
uv run python -m bases.orchestrix.web_gui_demo.app
# Open http://localhost:8050
```

## Technical Pattern Demos

### [Events & Commands](events_and_commands.md)
Basics of command/event separation, handler registration, and the Module protocol.

### [Tracing](tracing.md)
Distributed tracing with OpenTelemetry and Jaeger integration.

### [Validation](validation.md)
Input validation using built-in guard clauses and `ValidationError`.

### [Versioning](versioning.md)
Event schema evolution using upcasters and `UpcasterRegistry`.

### [GCP Integration](gcp_demo.md)
Google Cloud SQL, BigQuery, and Pub/Sub infrastructure adapters.


## Running Demos

All demos live in `bases/orchestrix/` and run with `uv`:

```bash
# Banking
uv run python -m bases.orchestrix.banking_demo.main

# E-Commerce
uv run python -m bases.orchestrix.ecommerce_demo.main

# Lakehouse (FastAPI)
uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app --reload

# Notifications
uv run python -m bases.orchestrix.notifications_demo.main

# Projections
uv run python -m bases.orchestrix.projection_demo.demo_projection

# Web GUI (Dash)
uv run python -m bases.orchestrix.web_gui_demo.app

# Events & Commands
uv run python -m bases.orchestrix.events_and_commands_demo.demo_events_and_commands

# Validation
uv run python -m bases.orchestrix.validation_demo.demo_validation

# Versioning
uv run python -m bases.orchestrix.versioning_demo.demo_versioning

# GCP
uv run python -m bases.orchestrix.gcp_demo.main
```


## Learning Path

1. **Events & Commands** → Learn message-driven basics
2. **Banking** → Understand event sourcing + aggregates
3. **E-Commerce** → Master sagas and distributed transactions
4. **Lakehouse** → Production patterns for compliance and data management
5. **Notifications** → Resilience: retries, backoff, dead letter queues
6. **Web GUI** → Visualize everything interactively
