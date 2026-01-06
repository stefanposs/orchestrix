
# Architecture Decision Log

This document records all significant architectural decisions for Orchestrix. We use the **AEK Model** (Context, Insight, Consequence) to capture the reasoning behind each decision.

---

## 1. Adoption of Polylith Architecture

**Context**
The project started with a traditional monolithic structure. As complexity grew, it became difficult to manage dependencies, share code between different deployment targets (e.g., API, Workers), and maintain a clear separation of concerns. We needed a way to modularize the codebase without the operational overhead of microservices.

**Insight**
Polylith offers a component-based architecture that separates code into:
- **Components**: Encapsulated logic blocks (building blocks).
- **Bases**: Entry points exposing public APIs (e.g., REST, CLI).
- **Projects**: Deployable artifacts that assemble components and bases.
This structure allows for a "Monorepo" development experience with the flexibility to deploy like microservices. It promotes code reuse and strict interface boundaries.

**Consequence**
- The codebase was restructured into `components/`, `bases/`, and `projects/`.
- Development workflow now uses `polylith-cli` and `uv` workspaces.
- Tests are co-located with components, improving test isolation.
- We can easily create new deployment artifacts by mixing and matching existing components.

---

## 2. Event Sourcing for State Management

**Context**
The domain requires high data integrity, auditability, and the ability to reconstruct past states. Traditional CRUD (Create, Read, Update, Delete) models lose historical context and intent (e.g., "Order Shipped" vs. just changing status to "Shipped"). We needed a system that captures *why* state changed, not just *what* changed.

**Insight**
Event Sourcing persists the state of an entity as a sequence of immutable state-changing events.
- It provides a perfect audit log out-of-the-box.
- It enables "Time Travel" debugging by replaying events up to a specific point.
- It decouples write models (Aggregates) from read models (Projections), allowing for optimized queries (CQRS).

**Consequence**
- Implemented `EventStore` interface and `Aggregate` base classes.
- All state changes must be captured as `Event` objects (e.g., `OrderCreated`, `PaymentProcessed`).
- Increased complexity in the storage layer (need to handle snapshots, versioning, and concurrency).
- Requires a projection engine to build read-optimized views for queries.

---

## 3. Asynchronous I/O (Asyncio)

**Context**
The system is designed to handle high throughput of events and messages. Many operations are I/O bound (database writes, message bus publishing). Synchronous blocking code would limit scalability and responsiveness under load.

**Insight**
Python's `asyncio` library provides a single-threaded, concurrent execution model that is ideal for I/O-bound applications. It allows the application to handle thousands of concurrent connections/operations without the overhead of OS threads.

**Consequence**
- The entire core architecture (`MessageBus`, `EventStore`, `ProjectionEngine`) is built using `async`/`await`.
- We use async-native libraries like `asyncpg` for PostgreSQL.
- Testing requires `pytest-asyncio`.
- Developers must be familiar with asynchronous programming patterns.

---

## 4. Python Dataclasses for Data Validation

**Context**
In a dynamic language like Python, passing dictionaries or untyped objects can lead to runtime errors and unclear data contracts. We needed a robust way to define schemas for Commands, Events, and Domain Objects, ensuring data validity at the boundaries.

**Insight**
Python's built-in `dataclass` decorator provides type-safe, ergonomic, and fast data structures. It enforces type hints, supports default values, and integrates well with serialization libraries. Using dataclasses keeps dependencies minimal and leverages native Python features.

**Consequence**
- All `Message`, `Command`, and `Event` classes are implemented as Python dataclasses.
- Type hints and default values ensure data validity and clarity.
- Serialization for the `EventStore` and `MessageBus` uses standard libraries (e.g., `asdict`, `json`).
- Provides clear, self-documenting data structures with minimal overhead.

---

## 5. Unified Tooling (uv & just)

**Context**
Python project management often involves a mix of tools (`pip`, `venv`, `poetry`, `make`, `bash` scripts), leading to fragmented workflows and "it works on my machine" issues. We needed a fast, reliable, and unified toolchain for dependency management and task execution.

**Insight**
- **uv**: A strictly faster replacement for pip/pip-tools/poetry, written in Rust. It handles workspace management efficiently.
- **just**: A modern command runner that is more user-friendly and cross-platform than `make`.

**Consequence**
- Adopted `uv` for all package and workspace management.
- Created a `justfile` as the single entry point for all development tasks (`just test`, `just lint`, `just build`).
- Significantly reduced CI/CD build times and simplified onboarding for new developers.

---

## 6. Infrastructure Agnosticism & EventSourcingDB Rationale

**Context**
The core domain logic should not be coupled to specific infrastructure technologies (e.g., PostgreSQL, RabbitMQ). We need the ability to swap infrastructure implementations (e.g., for testing or different deployment environments) without changing business logic.

**Insight**
The "Ports and Adapters" (Hexagonal) architecture pattern defines interfaces (Ports) for infrastructure needs, and specific implementations (Adapters) that fulfill them.

**Why EventSourcingDB from the native web?**
- Purpose-built for event sourcing and CQRS, not a repurposed general database
- Native CloudEvents support: perfect alignment with Orchestrix event model
- Built-in features: snapshots, upcasting, preconditions, EventQL for complex queries
- Operational simplicity: single binary, Docker/Kubernetes ready, no external brokers
- Air-gap and compliance friendly: works in isolated environments, no phone-home
- Professional support and free tier: commercial-grade reliability, but easy entry for small projects
- Future-proof: schema evolution, versioning, and observability (OpenTelemetry) out-of-the-box

**Consequence**
- Defined abstract base classes (Protocols) for `EventStore`, `MessageBus`, and `KeyValueStore`.
- Implemented `InMemory` adapters for fast testing and local development.
- Implemented `Postgres` adapters for production persistence.
- Implemented EventSourcingDB adapter for native event-driven persistence and advanced features.
- Tests can run against all adapters for speed, integration, and feature coverage.

---

## 7. Observability First

**Context**
In a distributed or event-driven system, debugging and understanding system behavior is challenging. Logs alone are insufficient to trace a request across multiple components or async tasks.

**Insight**
We need structured observability from day one, including:
- **Tracing**: To follow the path of a request/command.
- **Metrics**: To monitor system health and performance.
- **Logging**: To capture detailed context.

**Consequence**
- Integrated OpenTelemetry for distributed tracing.
- Integrated Prometheus for metrics collection.
- Structured logging with correlation IDs (Trace IDs) to link logs to traces.
- Added `test_observability.py` to ensure these features work correctly.

---

## 8. Python Version and Generics Syntax (2026-01-05)

**Context**
Orchestrix originally supported Python >=3.11,<3.14. The new generics syntax (PEP 695, e.g., `class Foo[T]: ...`) is only available from Python 3.12 onwards. For Python 3.11, the classic pattern with `TypeVar` and `Generic[T]` had to be used, which led to linter warnings and duplicate code.

**Insight**
As of January 2026, we officially support only Python >=3.12,<3.14. This allows us to use the modern PEP 695 syntax for generics throughout the codebase. The classic pattern is no longer needed. Benefits:
- Unified, modern syntax
- Less boilerplate, better readability
- No more linter warnings (Ruff, Ty)
- Future-proof for upcoming Python versions

**Consequence**
- All pyproject.toml and CI workflows now require Python >=3.12
- Migrated all generics to PEP 695 syntax
- Documentation and examples updated accordingly

---

## 9. Evaluation: Built-in Cloud & Integration Services (Open)

**Context**
Orchestrix is increasingly used in environments that require integration with cloud services and external APIs (monitoring, analytics, messaging, communication). There is demand for built-in adapters for services like Sentry, BigQuery, Cloud Storage, Cloud SQL, Pub/Sub, and SendGrid. However, adding these directly to the core may increase complexity and reduce flexibility for minimal deployments.

**Insight**
We are currently evaluating whether to provide built-in integrations for:
- Monitoring: Sentry (error tracking, performance monitoring)
- Data Services: Google BigQuery (analytics), Cloud Storage (snapshots), Cloud SQL (managed PostgreSQL)
- Messaging: Google Pub/Sub (event streaming, external integrations)
- Communication: SendGrid (email notifications, transactional emails)

Key questions:
- Should Orchestrix be "batteries included" with cloud integrations?
- Or should it stay minimal and let users build adapters as needed?

**Consequence**
- Decision pending. No built-in cloud integrations yet; users build adapters as needed.
- See README and TODO.md for ongoing discussion and community feedback.
