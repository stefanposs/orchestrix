
# Demos

Orchestrix includes production-ready demos that showcase real-world patterns for event-driven architectures. Each demo is self-contained and runnable.

## Practical Demos

### 🏦 [Banking](banking.md)
Account management with event sourcing, aggregates, sagas, and compensation flows.

### 🛒 [E-Commerce](ecommerce.md)
Order processing with multi-aggregate saga, inventory reservation, payment, and automatic rollback.

### 🏢 [Lakehouse Platform](lakehouse.md)
Self-service data platform with GDPR compliance, batch lifecycle, data contracts, and quality checks. Includes FastAPI REST API with SSE streaming.

### 🔔 [Notifications](notifications.md)
Resilient notification system with configurable retry policies, dead letter queue, and multi-channel delivery.

### 📊 [Projections](projection.md)
Read model construction from event streams — CQRS pattern with denormalized query models.

### 🖥️ Web GUI
Interactive Dash dashboard for exploring events, commands, and aggregate state in real time.

## Simple Demos (Technical Patterns)

### [Events & Commands](events_and_commands.md)
Basics of command/event separation and handler registration.

### [Tracing](tracing.md)
Distributed tracing with OpenTelemetry and Jaeger.

### [Validation](validation.md)
Input validation, error handling, and guard clauses.

### [Versioning](versioning.md)
Event schema evolution using upcasters and version compatibility.


## Running Demos

All demos live in `bases/orchestrix/` and run directly with `uv`:

```bash
# Banking
uv run python -m bases.orchestrix.banking_demo.main

# E-Commerce
uv run python -m bases.orchestrix.ecommerce_demo.main

# Lakehouse (FastAPI server)
uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app --reload

# Notifications
uv run python -m bases.orchestrix.notifications_demo.main

# Projections
uv run python -m bases.orchestrix.projection_demo.demo_projection

# Web GUI (Dash dashboard)
uv run python -m bases.orchestrix.web_gui_demo.app

# Events & Commands
uv run python -m bases.orchestrix.events_and_commands_demo.demo_events_and_commands

# Validation
uv run python -m bases.orchestrix.validation_demo.demo_validation

# Versioning
uv run python -m bases.orchestrix.versioning_demo.demo_versioning
```

## Demo Structure

Each demo follows a consistent pattern using the [Polylith](https://polylith.gitbook.io/) architecture:

```
bases/orchestrix/{demo}/
├── README.md              # Overview and quick start
├── __init__.py            # Module exports
├── models.py              # Commands, Events, Domain models
├── aggregate.py           # Aggregate root with business logic
├── handlers.py            # Command and event handlers
├── saga.py                # Saga orchestration (if applicable)
└── main.py                # Runnable entry point
```

## Learning Path

1. **Start with Events & Commands** — Learn the basics of message-driven design
2. **Move to Banking** — Understand event sourcing and aggregate patterns
3. **Study E-Commerce** — Master sagas and distributed transaction coordination
4. **Explore Lakehouse** — See production patterns for compliance and data management
5. **Try Notifications** — Learn resilience patterns, retries, and error handling
6. **Launch Web GUI** — Visualize everything interactively

