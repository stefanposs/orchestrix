# Orchestrix Library

The core library project for the Orchestrix framework.

## Overview
This project bundles the core components and infrastructure of Orchestrix into a distributable library.

## Components

### Core
- **Messaging**: Message bus, commands, events, and handlers.
- **Event Sourcing**: Aggregates, event store, snapshots, and projections.
- **Execution**: Sagas and retry policies.
- **Common**: Logging, validation, and observability.

### Infrastructure
- **Memory**: In-memory implementations for testing.
- **PostgreSQL**: Production-ready event store and connection pooling.
- **Observability**: Prometheus metrics and Jaeger tracing.

## Usage
This project is intended to be built as a wheel and installed in other projects.
