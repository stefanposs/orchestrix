
# GCP BigQuery Event Store for Orchestrix

This component provides an asynchronous Event Store backend for Orchestrix using Google BigQuery.

## Features
- Async event storage and retrieval
- Stores all events as JSON strings
- Secure: dataset and table names are strictly validated
- Uses only Python standard library and google-cloud-bigquery
- Designed for dataclasses (no pydantic dependency)

## Configuration
Set environment variables or pass directly:

```
BQ_DATASET=orchestrix
BQ_TABLE=orchestrix_events
```

## Usage
- Use as a drop-in replacement for any EventStore Protocol implementation
- See `store.py` for API and integration details

## Integration Notes
- The BigQuery Python client is not async, so calls are wrapped using `run_in_executor`
- All events are versioned and auditable

> Implementation is in progress. See `store.py` for current API and usage examples.
