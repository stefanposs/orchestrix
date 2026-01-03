# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Orchestrix framework
- Core message abstractions (Message, Command, Event)
- Module system for encapsulating domain logic
- InMemoryMessageBus for synchronous message routing
- InMemoryEventStore for event persistence
- Full type annotations with py.typed
- CloudEvents-compatible message structure
- Comprehensive test suite with 100% coverage
- CI/CD pipeline with GitHub Actions
- Documentation with MkDocs Material
- Pre-commit hooks for code quality
- Contributing guidelines and Code of Conduct

## [0.1.0] - 2026-01-03

### Added
- Initial public release
- Core framework with message bus and event store
- Example OrderModule demonstrating usage
- Full documentation and examples

[Unreleased]: https://github.com/stefanposs/orchestrix/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/stefanposs/orchestrix/releases/tag/v0.1.0
