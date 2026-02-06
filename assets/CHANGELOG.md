# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Web GUI demo — interactive Dash dashboard for event exploration, command execution, and aggregate inspection
- SSE (Server-Sent Events) streaming for lakehouse FastAPI demo
- GCP integrations: BigQuery, Cloud SQL, Pub/Sub event store adapters

### Changed
- All documentation converted to English
- MkDocs pages updated for Python 3.12+ requirement

## [0.1.0] - 2026-01-03

### Added
- **Core Framework**
  - `Command`, `Event`, `Message` base classes (CloudEvents-compatible, frozen dataclasses)
  - `MessageBus` and `AsyncMessageBus` with handler registration and publish/subscribe
  - `CommandHandler` base class for typed command processing
  - `Module` for encapsulating domain logic
  - `DeadLetterQueue` for failed message handling
- **Event Sourcing**
  - `AggregateRoot` with `_apply_event()` / `_when_*()` pattern
  - `AggregateRepository` with optimistic locking
  - `EventStore` protocol with append/load/snapshot support
  - `ProjectionEngine` for building read models from event streams
  - `Snapshot` support for aggregate state caching
  - `EventUpcaster` and `UpcasterRegistry` for schema evolution
- **Infrastructure Backends**
  - `InMemoryEventStore` and `InMemoryMessageBus` (sync + async)
  - `PostgreSQLEventStore` with JSONB, connection pooling, and migrations
  - `EventSourcingDBStore` with native CloudEvents and EventQL
- **Observability**
  - Prometheus metrics via `PrometheusMetrics`
  - OpenTelemetry tracing via `JaegerTracer`
  - `StructuredLogger` with context propagation
- **Resilience**
  - Retry policies: `ExponentialBackoff`, `FixedDelay`, `LinearBackoff`, `NoRetry`
  - Native validation helpers (`validate_not_empty`, `validate_positive`, etc.)
- **Sagas**
  - `Saga` base class for long-running business processes with compensation
- **Demos**
  - Banking: Account management with transfers and saga compensation
  - E-Commerce: Multi-aggregate order processing with rollback
  - Lakehouse: Self-service data platform with FastAPI, batch lifecycle, GDPR
  - Notifications: Multi-channel delivery with retries and DLQ
  - Projections, Validation, Versioning, Events & Commands, Tracing
- **Developer Experience**
  - Polylith architecture (components, bases, projects)
  - Full type annotations with `py.typed`
  - Benchmark suite with pytest-benchmark
  - MkDocs documentation site with mkdocs-material
  - `justfile` for development workflow automation
  - Ruff linting, ty type checking, pytest with coverage

[Unreleased]: https://github.com/stefanposs/orchestrix/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/stefanposs/orchestrix/releases/tag/v0.1.0
