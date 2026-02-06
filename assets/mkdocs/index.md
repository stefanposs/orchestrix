---


# Orchestrix — Your Processes. Your Data. Your Control.

**Orchestrix is the event-sourcing framework for AI-driven, enterprise-grade, rapidly evolving Python systems. Model, manage, and version your business processes — guaranteeing data quality, auditability, and governance.**

In a world of AI-accelerated development, your processes and data need a solid, versioned foundation. Orchestrix keeps them consistent, auditable, and under your control while your systems evolve at AI speed.

**Get Started:**

- [Installation & Quick Setup](getting-started/installation.md)
- [Core Concepts (Commands, Events, Aggregates)](getting-started/concepts.md)
- [Demos: Banking, E-Commerce, Lakehouse, Web GUI](demos/index.md)

---

## Why Orchestrix

Modern enterprises manage **hundreds of applications and tools**, each storing and interpreting data differently. Business knowledge becomes **fragmented**, trapped in multiple systems.

Traditional CRUD systems capture only the latest state — they **lose history, decisions, and rationale**. Orchestrix:

- Models **business processes as first-class citizens**
- Captures every change as a **versioned event**
- Enforces **contracts** for consistency, compliance, and data quality
- Maintains **ownership of knowledge** in the organization

Your processes are **digital assets**. Orchestrix ensures they remain so.

---

## Core Principles

1. **Process-Driven Systems** — Processes are modeled explicitly. Data and actions are secondary to the flow of business logic.
2. **Event Sourcing** — Every change is an event. History is preserved. Systems become audit-ready and reproducible.
3. **Commands & Events** — Commands trigger actions, Events record changes. Versioned contracts ensure backward compatibility.
4. **Infrastructure Abstraction** — Event stores, buses, monitoring, and logging can be swapped without affecting core logic.
5. **Ownership & Governance** — Knowledge resides with your teams, not with third-party tools.
6. **AI-Ready & Future-Proof** — Readable, maintainable, scalable. Supports rapid iteration and AI-enhanced workflows.

---

## Features

- **Modular Design** — Encapsulate domain logic in independent modules
- **Event Sourcing** — First-class support for event-sourced aggregates with optimistic locking
- **CloudEvents Compatible** — Immutable, metadata-rich messages
- **Pluggable Infrastructure** — Swap bus/store implementations easily
- **Type-Safe** — Full type annotations with `py.typed`
- **Simple API** — Minimal boilerplate, maximum productivity
- **Sagas** — Long-running business processes with compensation logic
- **Projections** — Build read models from event streams
- **Observability** — Built-in Prometheus metrics and OpenTelemetry tracing
- **Event Versioning** — Upcasters for evolving event schemas

---

## Quick Start

### Installation

```bash
pip install orchestrix
```

Or with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv add orchestrix
```

**Requires Python 3.12+**

### Basic Usage

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Command, Event
from orchestrix.core.eventsourcing.aggregate import AggregateRoot, AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus

# Define messages
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_name: str

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str

# Define aggregate
@dataclass
class Order(AggregateRoot):
    customer_name: str = ""
    status: str = "pending"

    def create(self, customer_name: str) -> None:
        self._apply_event(OrderCreated(
            order_id=self.aggregate_id,
            customer_name=customer_name,
        ))

    def _when_order_created(self, event: OrderCreated) -> None:
        self.customer_name = event.customer_name
        self.status = "created"

# Wire and execute
store = InMemoryEventStore()
repo = AggregateRepository(event_store=store)

order = Order(aggregate_id="ORD-001")
order.create("Alice")
repo.save(order)

loaded = repo.load(Order, "ORD-001")
assert loaded.customer_name == "Alice"
```

---

## Architecture

Orchestrix follows **Domain-Driven Design** and **CQRS/ES** principles:

- **Commands** represent intentions to change state
- **Events** represent facts that have occurred
- **Aggregates** enforce business rules and emit events
- **Message Bus** routes commands and events to handlers
- **Event Store** persists event streams for reconstruction

Learn more in the [Architecture Guide](development/architecture.md).

---

## Demos

Explore production-ready examples demonstrating real-world patterns:

- **[Banking](demos/banking.md)** — Account management with event sourcing
- **[E-Commerce](demos/ecommerce.md)** — Order processing with saga pattern
- **[Lakehouse Platform](demos/lakehouse.md)** — GDPR-compliant data lake with FastAPI
- **[Notifications](demos/notifications.md)** — Resilient notification system with retry + DLQ
- **[GCP Cloud](demos/gcp_demo.md)** — Google Cloud Pub/Sub and BigQuery integration
- **[Projections](demos/projection.md)** — CQRS read model projections
- **[Versioning](demos/versioning.md)** — Event schema evolution with upcasters

[**Browse All Demos →**](demos/index.md)

---

## Contributing

Contributions are welcome! See the [Contributing Guide](development/contributing.md) for development setup and workflow.

## License

MIT License — see [LICENSE](https://github.com/stefanposs/orchestrix/blob/main/LICENSE) for details.

## Support

- [Documentation](https://stefanposs.github.io/orchestrix)
- [Issue Tracker](https://github.com/stefanposs/orchestrix/issues)
- [Discussions](https://github.com/stefanposs/orchestrix/discussions)
