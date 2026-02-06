# Orchestrix

**Event-sourcing framework for building fast, auditable, AI-ready Python systems.**

[![CI](https://github.com/stefanposs/orchestrix/workflows/CI/badge.svg)](https://github.com/stefanposs/orchestrix/actions)
[![codecov](https://codecov.io/gh/stefanposs/orchestrix/branch/main/graph/badge.svg)](https://codecov.io/gh/stefanposs/orchestrix)
[![PyPI version](https://badge.fury.io/py/orchestrix.svg)](https://badge.fury.io/py/orchestrix)
[![Python Versions](https://img.shields.io/pypi/pyversions/orchestrix.svg)](https://pypi.org/project/orchestrix/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Your Processes. Your Data. Your Control.

## Quick Start

```bash
pip install orchestrix
# or with uv (recommended)
uv add orchestrix
```

**Requires Python 3.12+**

```python
from dataclasses import dataclass
from orchestrix import Command, Event, Module, CommandHandler
from orchestrix.infrastructure import InMemoryMessageBus, InMemoryEventStore

# Define domain messages
@dataclass(frozen=True)
class CreateOrder(Command):
    order_id: str
    total: float

@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    total: float

# Handle commands, emit events
class OrderHandler(CommandHandler[CreateOrder]):
    def handle(self, cmd: CreateOrder) -> list[Event]:
        return [OrderCreated(order_id=cmd.order_id, total=cmd.total)]

# Wire and run
bus = InMemoryMessageBus()
store = InMemoryEventStore()
bus.register_handler(CreateOrder, OrderHandler(store))
bus.publish(CreateOrder(order_id="ORD-001", total=149.99))
```

## Why Orchestrix?

Traditional CRUD loses business context. Orchestrix captures every state change as an immutable event — giving you full audit trails, time-travel debugging, and AI-ready data lineage.

| Capability | What You Get |
|---|---|
| **Event Sourcing** | Immutable event streams with optimistic locking |
| **CQRS** | Separated read/write models for optimal performance |
| **Sagas** | Distributed transactions with automatic compensation |
| **Projections** | Build read models from event streams |
| **Observability** | Prometheus metrics + OpenTelemetry tracing built-in |
| **CloudEvents** | Standards-compliant, metadata-rich messages |
| **Event Versioning** | Schema evolution with upcasters |
| **Pluggable Infra** | Swap stores and buses without changing domain logic |

## When to Use Orchestrix

**Best fit for:**
- Finance & compliance (audit trails, traceability)
- E-Commerce workflows (orders, inventory, payments)
- Data platforms & lakehouse architectures (lineage, GDPR)
- AI/ML pipelines (reproducible, versioned training data)
- Microservices with event-driven coordination

**Consider alternatives if:** simple CRUD with no complex business logic, or strong consistency is the only requirement.

## Architecture

Orchestrix follows a [Polylith](https://polylith.gitbook.io/) architecture with clear separation:

```
components/     # Reusable bricks (core logic + infrastructure adapters)
  core/         # messaging, eventsourcing, execution, common
  infrastructure/  # memory, postgres, eventsourcingdb, observability, gcp
bases/          # Deployable applications (demos & services)
projects/       # Deployment assemblies (thin wrappers referencing bases)
```

**Infrastructure backends:** InMemory (dev/test), PostgreSQL (production), EventSourcingDB (native CloudEvents)

## Demos

| Demo | Description | Run |
|---|---|---|
| 🏦 Banking | Account management, event sourcing, sagas | `uv run python -m bases.orchestrix.banking_demo.main` |
| 🛒 E-Commerce | Order processing, multi-aggregate saga, compensation | `uv run python -m bases.orchestrix.ecommerce_demo.main` |
| 🏢 Lakehouse | Enterprise data platform: SLA enforcement, executor backends, pipeline automation, GDPR | `uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app` |
| 🔔 Notifications | Retry policies, dead letter queue, multi-channel | `uv run python -m bases.orchestrix.notifications_demo.main` |
| 📊 Projections | Read models, CQRS, query denormalization | `uv run python -m bases.orchestrix.projection_demo.demo_projection` |
| 🖥️ Web GUI | Interactive dashboard (Dash) for event exploration | `uv run python -m bases.orchestrix.web_gui_demo.app` |

See the [full demo catalog](https://stefanposs.github.io/orchestrix/demos/) for walkthroughs and code.

## Documentation

| Resource | Link |
|---|---|
| Full Documentation | [stefanposs.github.io/orchestrix](https://stefanposs.github.io/orchestrix) |
| Installation | [Getting Started](https://stefanposs.github.io/orchestrix/getting-started/installation/) |
| Core Concepts | [Architecture Guide](https://stefanposs.github.io/orchestrix/getting-started/concepts/) |
| API Reference | [API Docs](https://stefanposs.github.io/orchestrix/api/core/) |
| Deployment Guide | [assets/deployment/APPLICATION_DEPLOYMENT.md](assets/deployment/APPLICATION_DEPLOYMENT.md) |
| Changelog | [assets/CHANGELOG.md](assets/CHANGELOG.md) |

## Development

```bash
# Install dependencies
just install

# Run full QA suite (lint + format + typecheck + test)
just qa

# Auto-fix formatting & lint issues
just fix

# Serve docs locally
just docs
```

## Roadmap

### Completed (v0.1.0)
Event Sourcing · CQRS · Sagas · Projections · Event Versioning · Snapshots · Retry Policies · Dead Letter Queue · Async Support · PostgreSQL Backend · EventSourcingDB Backend · OpenTelemetry Tracing · Prometheus Metrics · Connection Pooling · Benchmark Suite

### Under Consideration
See [TODO.md](TODO.md) — MongoDB/DynamoDB backends, parallel sagas, schema registry, admin CLI, and more.

## Contributing

Contributions welcome — see [CONTRIBUTING.md](.github/CONTRIBUTING.md). Areas of interest: new backends, saga patterns, real-world demos, cloud integrations, performance optimizations.

## License

MIT — see [LICENSE](LICENSE)
