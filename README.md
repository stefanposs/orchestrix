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

### Run Examples

```bash
# Basic order example
uv run examples/ecommerce/order_example.py

# Sagas (distributed transactions)
uv run examples/sagas/example.py

# Projections (read models)
uv run examples/projections/example.py

# Tracing with Jaeger
uv run examples/tracing/example.py

# Prometheus metrics
uv run examples/prometheus/example.py

# Event versioning
uv run examples/versioning/example.py
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
├── src/orchestrix/
│   ├── core/                        # Core framework
│   │   ├── __init__.py              # Public API exports
│   │   ├── aggregate.py             # AggregateRoot & AggregateRepository
│   │   ├── command_handler.py       # CommandHandler protocol
│   │   ├── dead_letter_queue.py     # Failed message handling
│   │   ├── event_store.py           # EventStore protocol
│   │   ├── exceptions.py            # Framework exceptions
│   │   ├── logging.py               # Structured logging
│   │   ├── message.py               # Message, Command, Event base classes
│   │   ├── message_bus.py           # MessageBus protocol
│   │   ├── messaging.py             # Message metadata helpers
│   │   ├── module.py                # Module protocol
│   │   ├── observability.py         # ObservabilityHooks protocol
│   │   ├── projection.py            # Projection & ProjectionEngine
│   │   ├── retry.py                 # RetryPolicy & RetryableError
│   │   ├── saga.py                  # Saga orchestration
│   │   ├── snapshot.py              # Snapshot protocol & strategies
│   │   ├── validation.py            # Message validation
│   │   ├── versioning.py            # Event upcasters
│   │   └── py.typed                 # Type marker
│   └── infrastructure/              # Implementations
│       ├── __init__.py              # Infrastructure exports
│       ├── async_inmemory_bus.py    # Async message bus
│       ├── async_inmemory_store.py  # Async event store
│       ├── connection_pool.py       # PostgreSQL connection pooling
│       ├── eventsourcingdb_store.py # EventSourcingDB backend
│       ├── inmemory_bus.py          # Sync message bus
│       ├── inmemory_store.py        # Sync event store
│       ├── memory.py                # Shared memory utilities
│       ├── postgres_store.py        # PostgreSQL backend
│       ├── prometheus_metrics.py    # Prometheus metrics
│       └── tracing.py               # OpenTelemetry tracing
├── examples/                        # Production-ready examples
│   ├── banking/                     # Banking domain (accounts, transfers)
│   ├── ecommerce/                   # E-commerce (orders, inventory, shipping)
│   ├── projections/                 # Read model patterns
│   ├── sagas/                       # Distributed transaction examples
│   ├── tracing/                     # Observability examples
│   └── versioning/                  # Event schema evolution
└── tests/                           # 404+ tests, 84% coverage
    ├── unit/                        # Unit tests
    ├── integration/                 # Integration tests
    └── conftest.py                  # Shared fixtures
```

## Documentation

- [Changelog](docs/CHANGELOG.md)
- [Contributing](.github/CONTRIBUTING.md)
- [Security Policy](.github/SECURITY.md)
- [Code of Conduct](.github/CODE_OF_CONDUCT.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

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

### Planned Features

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

### Under Consideration

#### Cloud & Integration Services (Decision Pending)
We're evaluating whether to provide built-in integrations for:
- **Monitoring**: Sentry (error tracking, performance monitoring)
- **Data Services**: Google BigQuery (analytics), Cloud Storage (snapshots), Cloud SQL (managed PostgreSQL)
- **Messaging**: Google Pub/Sub (event streaming, external integrations)
- **Communication**: SendGrid (email notifications, transactional emails)

**Philosophy Question**: Should Orchestrix be "batteries included" with cloud integrations, or stay minimal and let users build adapters?

See [TODO.md](TODO.md) for full list of ideas and discussion points.

#### DevOps Automation
- **Dependabot**: Automated dependency updates and security scanning
- **Enhanced CI/CD**: Matrix testing (Python 3.11-3.13, multiple OS), coverage reporting
- **PyPI Publishing**: Automated releases on git tags with changelog generation
- **Documentation CD**: Auto-deploy docs with PR previews

#### Future Enhancements
- **Event Replay System**: Time-travel debugging and event filtering
- **Multi-Tenant Support**: Isolated event streams per tenant
- **Event Encryption**: At-rest encryption with KMS integration
- **Schema Registry**: Avro/Protobuf serialization with version compatibility
- **Additional Backends**: MongoDB, DynamoDB, Cosmos DB, Kafka, Redis, Elasticsearch
- **Saga Improvements**: Parallel steps, timeouts, visual orchestration UI
- **Developer Tools**: CLI tool, admin dashboard, VS Code extension
- **Advanced Testing**: Contract testing, chaos engineering, load testing framework

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
