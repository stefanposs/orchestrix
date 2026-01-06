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
**✅ When is Orchestrix a good fit?**

| Use Case                                 | Why Orchestrix?                                   |
|-------------------------------------------|---------------------------------------------------|
| **Finance**<br>(Banking, Payments)        | Full audit trails, compliance, traceability       |
| **E-Commerce**<br>(Orders, Inventory)     | Complex workflows, state tracking, integrations   |
| **Collaboration**<br>(Bookings, Scheduling)| Conflict handling, parallel edits, consistency    |
| **Domain-Driven Design**                  | Clear logic separation, semantic events           |
| **Microservices & Event-Driven**          | Decoupled, scalable, easy service integration     |
| **Analytics & AI/ML**                     | Complete event history, reproducible data         |

---

**Why Orchestrix?**

- **Data lineage:** Every change is an event—perfect for audit and analytics
- **Semantic events:** Capture *why*, not just *what* happened
- **Immutable history:** Reliable, append-only event streams
- **AI/ML ready:** Rich, consistent training data
- **Easy integration:** Stream events to data lakes or dashboards
- **Traceability:** Built-in audit and governance

> **Orchestrix makes your data traceable, reliable, and ready for analytics or AI.**



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
