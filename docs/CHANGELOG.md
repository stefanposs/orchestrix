# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Type Checking**: Integrated `ty` type checker from Astral for stricter type validation
- **Documentation**: Comprehensive production deployment guide for small/medium/large projects
- **Documentation**: Complete user guide covering project scaling strategies
- **DevOps**: GitHub Actions security scanning workflow (CodeQL, Bandit, TruffleHog)
- **DevOps**: Dependabot configuration for automated dependency updates
- **Planning**: TODO.md with 50+ feature ideas and cloud service integration decisions
- **Documentation**: "What Problem Does Orchestrix Solve?" and "When to Use" sections
- Optimistic locking for event stores (ConcurrencyError)
- Saga pattern implementation with compensation logic
- Projection engine with multiple backend support (InMemory, PostgreSQL)
- OpenTelemetry distributed tracing with Jaeger integration
- Prometheus metrics collection (message throughput, handler latency)
- Event versioning with upcasters for schema evolution
- PostgreSQL connection pooling for production workloads
- Comprehensive integration tests for PostgreSQL store
- Examples for sagas, projections, tracing, metrics, and versioning

### Changed
- **Documentation**: Updated project structure in README to reflect all 18 core modules
- **Documentation**: Updated mkdocs navigation to include production guides
- EventStore protocol now supports `expected_version` parameter
- All store implementations (InMemory, PostgreSQL) support optimistic locking
- Async stores now have consistent API with sync stores

### Fixed
- **Type Safety**: Fixed 46 ty type errors across saga, event store, aggregate modules
- **Type Safety**: Fixed 13 ty warnings with proper None checks and assertions
- InMemoryAsyncEventStore now properly supports expected_version parameter
- Memory compatibility layer passes through expected_version correctly

## [0.1.0] - 2026-01-03

### Added
- Initial public release
- Core framework with message bus and event store
- Example OrderModule demonstrating usage
- Full documentation and examples

[Unreleased]: https://github.com/stefanposs/orchestrix/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/stefanposs/orchestrix/releases/tag/v0.1.0
