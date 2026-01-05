# Architecture Decision Log

This document records all significant architectural decisions for Orchestrix. We use the **AEK Model** (Context, Insight, Consequence) to capture the reasoning behind each decision.

---

## 1. Adoption of Polylith Architecture

**Context (Ausgangslage)**
The project started with a traditional monolithic structure. As the complexity grew, it became difficult to manage dependencies, share code between different deployment targets (e.g., API, Workers), and maintain a clear separation of concerns. We needed a way to modularize the codebase without the operational overhead of microservices.

**Insight (Erkenntnis)**
Polylith offers a component-based architecture that separates code into:
- **Components**: Encapsulated logic blocks (building blocks).
- **Bases**: Entry points exposing public APIs (e.g., REST, CLI).
- **Projects**: Deployable artifacts that assemble components and bases.
This structure allows for a "Monorepo" development experience with the flexibility to deploy like microservices. It promotes code reuse and strict interface boundaries.

**Consequence (Konsequenz)**
- The codebase was restructured into `components/`, `bases/`, and `projects/`.
- Development workflow now uses `polylith-cli` and `uv` workspaces.
- Tests are co-located with components, improving test isolation.
- We can easily create new deployment artifacts by mixing and matching existing components.

---

## 2. Event Sourcing for State Management

**Context (Ausgangslage)**
The domain requires high data integrity, auditability, and the ability to reconstruct past states. Traditional CRUD (Create, Read, Update, Delete) models lose historical context and intent (e.g., "Order Shipped" vs. just changing status to "Shipped"). We needed a system that captures *why* state changed, not just *what* changed.

**Insight (Erkenntnis)**
Event Sourcing persists the state of an entity as a sequence of immutable state-changing events.
- It provides a perfect audit log out-of-the-box.
- It enables "Time Travel" debugging by replaying events up to a specific point.
- It decouples write models (Aggregates) from read models (Projections), allowing for optimized queries (CQRS).

**Consequence (Konsequenz)**
- Implemented `EventStore` interface and `Aggregate` base classes.
- All state changes must be captured as `Event` objects (e.g., `OrderCreated`, `PaymentProcessed`).
- Increased complexity in the storage layer (need to handle snapshots, versioning, and concurrency).
- Requires a projection engine to build read-optimized views for queries.

---

## 3. Asynchronous I/O (Asyncio)

**Context (Ausgangslage)**
The system is designed to handle high throughput of events and messages. Many operations are I/O bound (database writes, message bus publishing). Synchronous blocking code would limit scalability and responsiveness under load.

**Insight (Erkenntnis)**
Python's `asyncio` library provides a single-threaded, concurrent execution model that is ideal for I/O-bound applications. It allows the application to handle thousands of concurrent connections/operations without the overhead of OS threads.

**Consequence (Konsequenz)**
- The entire core architecture (`MessageBus`, `EventStore`, `ProjectionEngine`) is built using `async`/`await`.
- We use async-native libraries like `asyncpg` for PostgreSQL.
- Testing requires `pytest-asyncio`.
- Developers must be familiar with asynchronous programming patterns.

---

## 4. Pydantic for Data Validation

**Context (Ausgangslage)**
In a dynamic language like Python, passing dictionaries or untyped objects can lead to runtime errors and unclear data contracts. We needed a robust way to define schemas for Commands, Events, and Domain Objects, ensuring data validity at the boundaries.

**Insight (Erkenntnis)**
Pydantic provides data validation and settings management using Python type annotations. It is fast, ergonomic, and widely supported. It enforces type safety at runtime and provides easy serialization/deserialization (JSON).

**Consequence (Konsequenz)**
- All `Message`, `Command`, and `Event` classes inherit from Pydantic's `BaseModel`.
- Automatic validation of payloads upon instantiation.
- Simplifies serialization for the `EventStore` and `MessageBus`.
- Provides clear, self-documenting data structures.

---

## 5. Unified Tooling (uv & just)

**Context (Ausgangslage)**
Python project management often involves a mix of tools (`pip`, `venv`, `poetry`, `make`, `bash` scripts), leading to fragmented workflows and "it works on my machine" issues. We needed a fast, reliable, and unified toolchain for dependency management and task execution.

**Insight (Erkenntnis)**
- **uv**: A strictly faster replacement for pip/pip-tools/poetry, written in Rust. It handles workspace management efficiently.
- **just**: A modern command runner that is more user-friendly and cross-platform than `make`.

**Consequence (Konsequenz)**
- Adopted `uv` for all package and workspace management.
- Created a `justfile` as the single entry point for all development tasks (`just test`, `just lint`, `just build`).
- Significantly reduced CI/CD build times and simplified onboarding for new developers.

---

## 6. Infrastructure Agnosticism (Ports & Adapters)

**Context (Ausgangslage)**
The core domain logic should not be coupled to specific infrastructure technologies (e.g., PostgreSQL, RabbitMQ). We need the ability to swap infrastructure implementations (e.g., for testing or different deployment environments) without changing business logic.

**Insight (Erkenntnis)**
The "Ports and Adapters" (Hexagonal) architecture pattern defines interfaces (Ports) for infrastructure needs, and specific implementations (Adapters) that fulfill them.

**Consequence (Konsequenz)**
- Defined abstract base classes (Protocols) for `EventStore`, `MessageBus`, and `KeyValueStore`.
- Implemented `InMemory` adapters for fast testing and local development.
- Implemented `Postgres` adapters for production persistence.
- Tests can run against `InMemory` implementations for speed, or `Postgres` for integration verification.

---

## 7. Observability First

**Context (Ausgangslage)**
In a distributed or event-driven system, debugging and understanding system behavior is challenging. Logs alone are insufficient to trace a request across multiple components or async tasks.

**Insight (Erkenntnis)**
We need structured observability from day one, including:
- **Tracing**: To follow the path of a request/command.
- **Metrics**: To monitor system health and performance.
- **Logging**: To capture detailed context.

**Consequence (Konsequenz)**
- Integrated OpenTelemetry for distributed tracing.
- Integrated Prometheus for metrics collection.
- Structured logging with correlation IDs (Trace IDs) to link logs to traces.
- Added `test_observability.py` to ensure these features work correctly.
