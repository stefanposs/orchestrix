# Orchestrix

A modular, event-driven architecture framework for Python with CloudEvents-compatible messages.

[![CI](https://github.com/stefanposs/orchestrix/workflows/CI/badge.svg)](https://github.com/stefanposs/orchestrix/actions)
[![codecov](https://codecov.io/gh/stefanposs/orchestrix/branch/main/graph/badge.svg)](https://codecov.io/gh/stefanposs/orchestrix)
[![PyPI version](https://badge.fury.io/py/orchestrix.svg)](https://badge.fury.io/py/orchestrix)
[![Python Versions](https://img.shields.io/pypi/pyversions/orchestrix.svg)](https://pypi.org/project/orchestrix/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

### Run Demos

```bash
# Run Demos (see projects/ folder)

# Basic order demo
uv run projects/ecommerce_demo/main.py

# Sagas (distributed transactions)
uv run projects/ecommerce_demo/sagas_demo.py

# Projections (read models)
uv run projects/ecommerce_demo/projections_demo.py

# Tracing with Jaeger
uv run projects/ecommerce_demo/tracing_demo.py

# Prometheus metrics
uv run projects/ecommerce_demo/prometheus_demo.py

# Event versioning
uv run projects/ecommerce_demo/versioning_demo.py
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

## Project Structure

```
orchestrix/
├── components/
│   └── orchestrix/
│       ├── core/                    # Core framework (Interfaces, Message, Aggregate)
│       │   ├── common/              # Shared utilities (Logging, Validation, Retry)
│       │   ├── eventsourcing/       # Event sourcing logic (Aggregate, Store, Projection)
│       │   ├── execution/           # Execution patterns (Saga)
│       │   └── messaging/           # Messaging patterns (Bus, CommandHandler)
│       └── infrastructure/          # Infrastructure adapters
│           ├── eventsourcingdb/     # EventSourcingDB adapter
│           ├── memory/              # In-Memory adapters (Sync/Async)
│           ├── observability/       # Observability adapters (Prometheus, Jaeger)
│           └── postgres/            # PostgreSQL adapter
├── bases/
│   └── orchestrix/
│       ├── banking/                 # Banking Demo App
│       ├── ecommerce/               # E-commerce Demo App
│       ├── lakehouse/               # Lakehouse Demo App
│       └── notifications/           # Notifications Demo App
├── projects/
│   ├── orchestrix_lib/              # PyPI Package
│   ├── banking_demo/                # Deployable Service
│   ├── ecommerce_demo/              # Deployable Service
│   ├── lakehouse_demo/              # Deployable Service
│   └── notifications_demo/          # Deployable Service
├── examples/                        # Production-ready examples
│   ├── banking/                     # Banking domain (accounts, transfers)
│   ├── ecommerce/                   # E-commerce (orders, inventory, shipping)
│   ├── projections/                 # Read model patterns
│   ├── sagas/                       # Distributed transaction examples
│   ├── tracing/                     # Observability examples
│   └── versioning/                  # Event schema evolution
└── tests/                           # 404+ tests, 84% coverage
    ├── components/                  # Component tests
    ├── projects/                    # Integration tests
    └── benchmarks/                  # Performance benchmarks
```

## Documentation

- [Changelog](docs/CHANGELOG.md)
- [Contributing](.github/CONTRIBUTING.md)
- [Security Policy](.github/SECURITY.md)
- [Code of Conduct](.github/CODE_OF_CONDUCT.md)
- [Library Publishing Guide](docs/LIBRARY_PUBLISHING.md)
- [Application Deployment Guide](docs/deployment/APPLICATION_DEPLOYMENT.md)

## Roadmap & Future Plans

### ✅ Completed (v1.0)
- ✅ **Native Validation** - Dataclass validation without external dependencies
- ✅ **Async Support** - Concurrent message handling with asyncio
- ✅ **Enterprise Features** - Snapshots, retry policies, dead letter queue
- ✅ **Optimistic Locking** - Concurrency control for event stores
- ✅ **Sagas** - Long-running business processes with compensation
- ✅ **Projections** - Read model engine with multiple backends
- ✅ **OpenTelemetry Tracing** - Distributed tracing with Jaeger integration
- ✅ **Prometheus Metrics** - Production-grade metrics collection
- ✅ **Event Versioning** - Upcasters for schema evolution
- ✅ **Connection Pooling** - PostgreSQL connection management
- ✅ **PostgreSQL EventStore** - Production-ready backend (JSONB, locking, pooling, migrations)
- ✅ **EventSourcingDB Integration** - Native CloudEvents, snapshots, EventQL, Docker-ready

#### Benchmark Suite
- Performance testing framework with pytest-benchmark
- Baseline metrics (1k messages/sec, 10k event streams)
- Concurrent publish/subscribe benchmarks
- Memory profiling for large event streams

### Under Consideration

See [TODO.md](TODO.md) for full list of ideas and discussion points.

### Contributions Welcome

We're actively looking for contributors interested in:
- Enhancing EventSourcingDB backend with advanced features
- Adding more projection backends (Redis, Elasticsearch)
- Building advanced saga patterns (parallel execution, timeouts)
- Creating real-world example applications
- Performance optimizations and benchmarks
- Cloud service integrations (see TODO.md)
- DevOps automation (GitHub Actions, CI/CD)

See [Contributing](.github/CONTRIBUTING.md) for details.

## License

MIT
