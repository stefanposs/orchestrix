
# GCP Demo — Google Cloud Integration

Use Orchestrix event stores and message bus with Google Cloud services:
Cloud SQL (PostgreSQL), BigQuery, and Pub/Sub.

> **Source Code:**
> [`bases/orchestrix/gcp_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/gcp_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.gcp_demo.main
```

!!! note "Prerequisites"
    Requires a GCP project with Cloud SQL, BigQuery, and/or Pub/Sub enabled.
    Set Application Default Credentials: `gcloud auth application-default login`.

## Infrastructure Components

### Cloud SQL Event Store

Managed PostgreSQL-backed event store:

```python
from orchestrix.infrastructure.gcp_cloud_sql import GCPCloudSQLEventStore

store = GCPCloudSQLEventStore(
    connection_string="postgresql://user:pw@/db?host=/cloudsql/project:region:instance"
)
await store.initialize()
await store.save("stream-1", [my_event])
events = await store.load("stream-1")
```

### BigQuery Event Store

Append-only event store for analytics workloads:

```python
from orchestrix.infrastructure.gcp_bigquery import GCPBigQueryEventStore

store = GCPBigQueryEventStore(project_id="my-project", dataset_id="events")
```

### Pub/Sub Message Bus

Distributed message bus via Google Cloud Pub/Sub:

```python
from orchestrix.infrastructure.gcp_pubsub import GCPPubSub

bus = GCPPubSub(project_id="my-project", topic_id="orchestrix-events")
```

## Code Structure

```
bases/orchestrix/gcp_demo/
├── main.py          # CloudSQL + BigQuery demo
├── pubsub_demo.py   # Pub/Sub message distribution demo
└── README.md
```

## Related

- [Event Store Guide](../guide/event-store.md) — Compare store implementations
- [Production Deployment](../guide/production-deployment.md) — Cloud deployment patterns
