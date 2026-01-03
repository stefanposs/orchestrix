# Orchestrix

**A modular, event-driven architecture framework for Python with CloudEvents-compatible messages.**

> 🎉 **Live-Demo!** Diese Seite wird automatisch aktualisiert wenn du sie bearbeitest.

[![CI](https://github.com/stefanposs/orchestrix/workflows/CI/badge.svg)](https://github.com/stefanposs/orchestrix/actions)
[![codecov](https://codecov.io/gh/stefanposs/orchestrix/branch/main/graph/badge.svg)](https://codecov.io/gh/stefanposs/orchestrix)
[![PyPI version](https://badge.fury.io/py/orchestrix.svg)](https://badge.fury.io/py/orchestrix)
[![Python Versions](https://img.shields.io/pypi/pyversions/orchestrix.svg)](https://pypi.org/project/orchestrix/)

---

## Features

- 🎯 **Modular Design** - Encapsulate domain logic in independent modules
- 📦 **Event Sourcing** - First-class support for event-sourced aggregates
- ☁️ **CloudEvents Compatible** - Immutable, metadata-rich messages
- 🔌 **Pluggable Infrastructure** - Swap bus/store implementations easily
- 🧪 **Type-Safe** - Full type annotations with `py.typed`
- 🚀 **Simple API** - Minimal boilerplate, maximum productivity

## Quick Start

### Installation

```bash
pip install orchestrix
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add orchestrix
```

### Basic Usage

```python
from orchestrix.infrastructure import InMemoryMessageBus, InMemoryEventStore
from examples.order_module import OrderModule, CreateOrder

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
