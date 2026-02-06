---


# Orchestrix — Your Processes. Your Data. Your Control.

**Orchestrix is the event-sourcing framework for AI-driven, enterprise-grade, rapidly evolving Python systems. Model, manage, and version your business processes — guaranteeing data quality, auditability, and governance.**

In a world of AI-accelerated development, your processes and data need a solid, versioned foundation. Orchestrix keeps them consistent, auditable, and under your control while your systems evolve at AI speed.


**Get Started:**

- [Installation & Quick Setup](getting-started/installation.md)
- [Core Concepts (Commands, Events, Aggregates)](getting-started/concepts.md)
- [Demos: Banking, E-Commerce, Lakehouse, Web GUI](demos/index.md)



## 1️⃣ Why Orchestrix

Modern enterprises rarely operate a single system. Instead, they manage **hundreds of applications and tools**, each storing and interpreting data differently. Business knowledge often becomes **fragmented**, trapped in multiple tools, leaving organizations blind to their own data quality and process behavior.

Traditional CRUD systems capture only the latest state. They **lose history, decisions, and rationale**. In contrast, Orchestrix:

- Models **business processes as first-class citizens**
- Captures every change as a **versioned event**
- Enforces **contracts** to ensure consistency, compliance, and data quality
- Maintains **ownership of knowledge** in the organization

In times of AI-driven development, rapid prototyping, and evolving systems, **having a clear, scalable, maintainable architecture is critical**. Orchestrix ensures that your processes are **not only digital assets, but also your stable foundation for innovation**.

Your processes are **digital assets**. Orchestrix ensures they remain so.


## 2️⃣ Core Principles

1. **Process-Driven Systems**
    * Processes are modeled explicitly. Data and actions are secondary to the flow of business logic.
2. **Event Sourcing**
    * Every change is an event. History is preserved. Systems become **audit-ready and reproducible**.
3. **Commands & Events**
    * Commands trigger actions
    * Events record changes
    * Versioned contracts ensure backward compatibility and safe evolution
4. **Infrastructure Abstraction**
    * Event stores, buses, monitoring, and logging can be swapped without affecting core logic.
5. **Ownership & Governance**
    * Knowledge resides with your teams, not with third-party tools or ad-hoc scripts.
6. **AI-Ready & Future-Proof**
    * Framework is **readable, maintainable, scalable, extensible**
    * Supports rapid iteration, modern tooling, and AI-enhanced workflows
    * Ensures business processes remain **robust foundations**, even as tools, pipelines, and models evolve


## Features

- 🎯 **Modular Design** - Encapsulate domain logic in independent modules
- 📦 **Event Sourcing** - First-class support for event-sourced aggregates with optimistic locking
- ☁️ **CloudEvents Compatible** - Immutable, metadata-rich messages
- 🔌 **Pluggable Infrastructure** - Swap bus/store implementations easily
- 🧪 **Type-Safe** - Full type annotations with `py.typed`
- 🚀 **Simple API** - Minimal boilerplate, maximum productivity
- 🔄 **Sagas** - Long-running business processes with compensation logic
- 📊 **Projections** - Build read models from event streams
- 📈 **Observability** - Built-in Prometheus metrics and OpenTelemetry tracing
- 🔢 **Event Versioning** - Upcasters for evolving event schemas

## Quick Start

### Installation

```bash
# Basic installation
pip install orchestrix

# With PostgreSQL support
pip install orchestrix[postgres]

# With observability (Prometheus + OpenTelemetry tracing)
pip install orchestrix[observability]
```

Or with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv add orchestrix
```

**Requires Python 3.12+**

### Basic Usage

```python
from orchestrix.infrastructure import InMemoryMessageBus, InMemoryEventStore
from .order_module import OrderModule, CreateOrder

# Setup infrastructure
bus = InMemoryMessageBus()
store = InMemoryEventStore()

# Register module
module = OrderModule()
module.register(bus, store)

# Execute command
bus.publish(CreateOrder(
    order_id="ORD-001",
    customer_name="Alice",
    total_amount=149.99
))
```

## Documentation

Full documentation: [stefanposs.github.io/orchestrix](https://stefanposs.github.io/orchestrix)

## Example

Create a simple order management system in minutes:

```python
from dataclasses import dataclass
from orchestrix import Command, Event, Module

@dataclass(frozen=True)
class CreateOrder(Command):
    order_id: str
    customer_name: str
    total_amount: float

@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str
    total_amount: float

# Full example in examples/order_module.py
```

## Architecture

Orchestrix follows **Domain-Driven Design** and **CQRS/ES** principles:

- **Commands** represent intentions to change state
- **Events** represent facts that have occurred
- **Aggregates** enforce business rules and emit events
- **Message Bus** routes commands and events to handlers
- **Event Store** persists event streams for reconstruction

Learn more in the [Architecture Guide](development/architecture.md).


## Demos

Explore production-ready examples demonstrating real-world patterns:

- 🏦 **[Banking](demos/banking.md)** - Account management with event sourcing
- 🛒 **[E-Commerce](demos/ecommerce.md)** - Order processing with saga pattern
- 🏢 **[Lakehouse Platform](demos/lakehouse.md)** - GDPR-compliant data lake
- 🔔 **[Notifications](demos/notifications.md)** - Resilient notification system

[**Browse All Demos →**](demos/index.md)


## Contributing

Contributions are welcome! Please read our [Contributing Guide](https://github.com/stefanposs/orchestrix/blob/main/.github/CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](https://github.com/stefanposs/orchestrix/blob/main/LICENSE) for details.

## Support

- 📖 [Documentation](https://orchestrix.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/stefanposs/orchestrix/issues)
- 💬 [Discussions](https://github.com/stefanposs/orchestrix/discussions)