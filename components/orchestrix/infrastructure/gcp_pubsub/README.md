
# GCP Pub/Sub Integration for Orchestrix

This component provides integration with Google Cloud Pub/Sub for event-driven messaging in Orchestrix.

## Features
- Async publish and subscribe methods
- Uses google-cloud-pubsub and testcontainers for local testing
- Secure: environment-based configuration
- Designed for dataclasses (no pydantic dependency)

## Configuration
Set environment variables or pass directly:

```
PUBSUB_EMULATOR_HOST=localhost:8085
```

## Usage
- Use as a drop-in replacement for any message bus or event bus implementation
- See `store.py` and `pubsub.py` for API and integration details

## Integration Notes
- Supports local testing with Pub/Sub emulator via testcontainers
- All messages are versioned and auditable

> See `store.py` and `pubsub.py` for current API and usage examples.
