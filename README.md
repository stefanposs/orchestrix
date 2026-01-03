# Orchestrix

A modular, event-driven architecture framework for Python with CloudEvents-compatible messages.

[![CI](https://github.com/stefanposs/orchestrix/workflows/CI/badge.svg)](https://github.com/stefanposs/orchestrix/actions)
[![codecov](https://codecov.io/gh/stefanposs/orchestrix/branch/main/graph/badge.svg)](https://codecov.io/gh/stefanposs/orchestrix)
[![PyPI version](https://badge.fury.io/py/orchestrix.svg)](https://badge.fury.io/py/orchestrix)
[![Python Versions](https://img.shields.io/pypi/pyversions/orchestrix.svg)](https://pypi.org/project/orchestrix/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
# Development mode
pip install -e .
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

### Run Example

```bash
# With uv
uv run examples/run_order_example.py

# Or using just
just example
```

## Architecture

### Core Concepts

- **Message**: Immutable CloudEvents-compatible base class
- **Command**: Intent to perform an action
- **Event**: Fact that has occurred
- **Aggregate**: Domain entity that raises events
- **Module**: Encapsulates domain logic and registration

### Infrastructure

- **MessageBus**: Routes commands/events to handlers
- **EventStore**: Persists and retrieves event streams

### Creating a New Module

Use this prompt with GitHub Copilot:

```text
You are implementing a new Orchestrix module.

Create:
- Module: [YourModule]
- Aggregate: [YourAggregate]
- Commands: [YourCommand1, YourCommand2]
- Events: [YourEvent1, YourEvent2]

Rules:
- Use CloudEvents-compatible immutable messages
- Commands and Events inherit from orchestrix Message
- Aggregate raises events, no IO
- CommandHandlers persist events and publish them via MessageBus
- Register everything inside [YourModule]
- Add simple print handlers for all events
```

## Project Structure

```
orchestrix/
├── src/orchestrix/          # Core framework
│   ├── message.py           # Message base classes
│   ├── module.py            # Module protocol
│   ├── message_bus.py       # MessageBus protocol
│   ├── event_store.py       # EventStore protocol
│   ├── command_handler.py   # CommandHandler protocol
│   ├── py.typed             # Type marker
│   └── infrastructure/      # Implementations
│       ├── inmemory_bus.py
│       └── inmemory_store.py
└── examples/
    ├── order_module.py      # Example module
    └── run_order_example.py # Runnable demo
```

## License

MIT
