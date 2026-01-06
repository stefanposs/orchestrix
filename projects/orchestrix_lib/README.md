# Orchestrix Library

A modular, event-driven event sourcing library for Python.

## Overview
Orchestrix helps you build scalable, maintainable, and testable systems by combining event sourcing, CQRS, and asynchronous messaging. It is designed for complex business domains, microservices, and distributed workflows.

## Problem Statement
Building robust, auditable, and extensible business systems is hard. Orchestrix solves this by:
- Decoupling business logic from infrastructure
- Enabling full event history and traceability
- Supporting asynchronous, event-driven workflows
- Making testing and local development easy (in-memory backends)
- Providing production-ready persistence and observability

## Components

### Core
- **Messaging**: Message bus, commands, events, and handlers
- **Event Sourcing**: Aggregates, event store, snapshots, and projections
- **Execution**: Sagas and retry policies
- **Common**: Logging, validation, and observability

### Infrastructure
- **Memory**: In-memory implementations for testing
- **PostgreSQL**: Production-ready event store and connection pooling
- **Observability**: Prometheus metrics and Jaeger tracing

## Usage
Install the built wheel in your project and use the provided building blocks to implement your own event-driven, event-sourced applications.
