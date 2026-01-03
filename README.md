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

## Documentation

- [Changelog](docs/CHANGELOG.md)
- [Contributing](.github/CONTRIBUTING.md)
- [Security Policy](.github/SECURITY.md)
- [Code of Conduct](.github/CODE_OF_CONDUCT.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Roadmap & Future Plans

### In Progress
- ✅ **Native Validation** - Dataclass validation without external dependencies (v1.0)
- ✅ **Async Support** - Concurrent message handling with asyncio (v1.0)
- ✅ **Enterprise Features** - Snapshots, retry policies, dead letter queue (v1.0)

### Planned Features

#### Observability (Optional Dependencies)
- **OpenTelemetry Integration** - Distributed tracing for message flows
  - Automatic span creation for command/event handling
  - Trace context propagation via CloudEvents metadata
  - Integration with Jaeger, Zipkin, or cloud-native tracing
  - Optional dependency: `pip install orchestrix[tracing]`
  
- **Prometheus Metrics** - Production-grade metrics collection
  - Message throughput (commands/events per second)
  - Handler execution latency (p50, p95, p99)
  - Event store performance (read/write operations)
  - Optional dependency: `pip install orchestrix[metrics]`

#### Production Event Store Backends

##### PostgreSQL EventStore
- **Native PostgreSQL Backend** - Production-ready event persistence
  - JSONB storage for event data (efficient queries)
  - Optimistic concurrency with version columns
  - Aggregate-level locking with `SELECT FOR UPDATE`
  - Connection pooling via asyncpg
  - Migration scripts included
  - Optional dependency: `pip install orchestrix[postgres]`

##### EventSourcingDB Integration
- **EventSourcingDB Backend** - Purpose-built event sourcing database
  - Native CloudEvents compatibility (perfect alignment with Orchestrix)
  - Built-in snapshots (events-as-snapshots pattern)
  - Preconditions support (optimistic concurrency)
  - EventQL queries for complex read models
  - Docker/Kubernetes ready with official Python client
  - Free tier: 25,000 events (ideal for small-medium projects)
  - Optional dependency: `pip install orchestrix[eventsourcingdb]`
  
**Why EventSourcingDB?**
- **Designed for Event Sourcing** - Purpose-built database, not adapted from general-purpose storage
- **CloudEvents Native** - Same event model as Orchestrix (source, subject, type, data)
- **Operational Simplicity** - Single binary, Docker image, or Kubernetes deployment
- **No External Dependencies** - No brokers, no coordination services required
- **Air-Gap Friendly** - Works in isolated environments (license file-based, no phone-home)
- **Read-Only Mode** - After license expiry, data remains accessible (fail-safe behavior)
- **Professional Support** - Commercial product with enterprise-grade support options

**EventSourcingDB Comparison:**
| Feature | PostgreSQL | EventSourcingDB | InMemory |
|---------|-----------|-----------------|----------|
| Production Ready | ✅ | ✅ | ❌ |
| CloudEvents Native | ⚠️ (JSONB) | ✅ (Built-in) | ✅ |
| Snapshots | Custom | ✅ (Events-as-snapshots) | ✅ |
| Preconditions | Custom | ✅ (Built-in) | ❌ |
| Query Language | SQL | EventQL | Python |
| Observability | Custom | OpenTelemetry | None |
| Licensing | Open Source | Commercial (Free <25k events) | MIT |

**Migration Path:**
1. **Development**: Start with `InMemoryEventStore` (zero setup)
2. **Testing**: Use PostgreSQL for integration tests (pgvector/Docker)
3. **Production Small**: Deploy EventSourcingDB free tier (<25k events)
4. **Production Large**: Scale with EventSourcingDB commercial or PostgreSQL cluster

#### Advanced Examples
- **E-Commerce System** - Multi-aggregate saga patterns
- **Banking Application** - Event-sourced accounts with projections
- **Notification Service** - Async event handlers with retry logic

#### Benchmark Suite
- Performance testing framework with pytest-benchmark
- Baseline metrics (1k messages/sec, 10k event streams)
- Concurrent publish/subscribe benchmarks
- Memory profiling for large event streams

### Contributions Welcome

We're actively looking for contributors interested in:
- Implementing EventSourcingDB backend (`src/orchestrix/infrastructure/eventsourcingdb_store.py`)
- Adding OpenTelemetry tracing decorators
- Building Prometheus metrics exporters
- Creating real-world example applications

See [Contributing](.github/CONTRIBUTING.md) for details.

## License

MIT
