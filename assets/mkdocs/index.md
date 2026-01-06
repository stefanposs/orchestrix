# Orchestrix

**A modular, event-driven architecture framework for Python with CloudEvents-compatible messages.**

[![CI](https://github.com/stefanposs/orchestrix/workflows/CI/badge.svg)](https://github.com/stefanposs/orchestrix/actions)
[![codecov](https://codecov.io/gh/stefanposs/orchestrix/branch/main/graph/badge.svg)](https://codecov.io/gh/stefanposs/orchestrix)
[![PyPI version](https://badge.fury.io/py/orchestrix.svg)](https://badge.fury.io/py/orchestrix)
[![Python Versions](https://img.shields.io/pypi/pyversions/orchestrix.svg)](https://pypi.org/project/orchestrix/)

---

## What Problem Does Orchestrix Solve?

Traditional CRUD applications struggle with:
- **Lost Business Context** - Database updates don't capture *why* changes happened
- **Difficult Auditing** - No automatic audit trail of state changes
- **Complex Workflows** - Hard to coordinate multi-step business processes across services
- **Scalability Limits** - Tight coupling makes it hard to scale components independently
- **Debugging Nightmares** - Hard to reproduce production issues without event history

**Orchestrix provides:**
- **Event Sourcing** - Store every state change as an immutable event, never lose context
- **CQRS** - Separate read and write models for optimal performance
- **Sagas** - Reliable distributed transactions with automatic compensation
- **Time-Travel Debugging** - Replay events to any point in time
- **Built-in Observability** - Metrics, tracing, and audit logs out of the box

## When to Use Orchestrix

**✅ Perfect for:**
- Financial systems requiring full audit trails (banking, payments, trading)
- E-commerce with complex order workflows (inventory, payments, shipping)
- Collaborative applications needing conflict resolution (booking systems, reservations)
- Domain-Driven Design implementations with rich domain logic
- Microservices architectures requiring event-driven communication
- Systems where understanding *how* you got to current state matters

**⚠️ Consider alternatives if:**
- Simple CRUD with no complex business logic
- Performance is critical and eventual consistency is unacceptable
- Team lacks experience with event-driven patterns
- Small projects where event sourcing overhead isn't justified

---

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

# With observability (Prometheus + Tracing)
pip install orchestrix[observability]
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add orchestrix
```

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

Full documentation is available at [orchestrix.readthedocs.io](https://orchestrix.readthedocs.io)

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

---

## Examples

Explore production-ready examples demonstrating real-world patterns:

- 🏦 **[Banking](examples/banking.md)** - Account management with event sourcing
- 🛒 **[E-Commerce](examples/ecommerce.md)** - Order processing with saga pattern
- 🏢 **[Lakehouse Platform](examples/lakehouse-gdpr.md)** - GDPR-compliant data lake
- 🔔 **[Notifications](examples/notifications.md)** - Resilient notification system

[**Browse All Examples →**](examples/index.md)

---

## Contributing

Contributions are welcome! Please read our [Contributing Guide](https://github.com/stefanposs/orchestrix/blob/main/.github/CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](https://github.com/stefanposs/orchestrix/blob/main/LICENSE) for details.

## Support

- 📖 [Documentation](https://orchestrix.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/stefanposs/orchestrix/issues)
- 💬 [Discussions](https://github.com/stefanposs/orchestrix/discussions)
