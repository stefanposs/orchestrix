# GCP Demo

Demonstration of Orchestrix integration with Google Cloud technologies and testcontainers for local testing.

## Overview
This project contains demo scenarios for:
- **BigQuery**: Event sourcing with Google BigQuery as async EventStore
- **Cloud SQL (PostgreSQL)**: Managed, ACID-compliant event storage
- **Pub/Sub**: Event-driven messaging (via testcontainers)

## Features
- Event sourcing with BigQuery and Cloud SQL
- Example usage of GCP services in Orchestrix
- Local integration tests with testcontainers for BigQuery, Cloud SQL, and Pub/Sub

## Usage
Run the demo using the CLI or directly via Python:

```bash
uv run python -m orchestrix.gcp_demo.bigquery_demo
uv run python -m orchestrix.gcp_demo.cloudsql_demo
uv run python -m orchestrix.gcp_demo.pubsub_demo
```

## Configuration
See the respective README files in:
- components/orchestrix/infrastructure/gcp_bigquery
- components/orchestrix/infrastructure/gcp_cloud_sql
- components/orchestrix/infrastructure/gcp_pubsub

## Requirements
- google-cloud-bigquery
- asyncpg
- psycopg2-binary
- python-dotenv
- testcontainers[google-cloud]

## GCP Technologies Used
- BigQuery
- Cloud SQL (PostgreSQL)
- Pub/Sub

## Example Code
### BigQuery
```python
from orchestrix.infrastructure.gcp_bigquery.store import GCPBigQueryEventStore
store = GCPBigQueryEventStore()
await store.append("stream1", {"type": "OrderCreated", "data": {"order_id": 123}})
async for event in store.load("stream1"):
	print(event)
```

### Cloud SQL
```python
from orchestrix.infrastructure.gcp_cloud_sql.gcp_cloud_sql_store import GCPCloudSQLStore
store = GCPCloudSQLStore()
await store.append("stream2", {"type": "OrderCreated", "data": {"order_id": 456}})
async for event in store.load("stream2"):
	print(event)
```

### Pub/Sub (Testcontainers)
```python
from testcontainers.google.pubsub import PubSubContainer
with PubSubContainer() as pubsub:
	# Example: connect to local Pub/Sub emulator for integration tests
	endpoint = pubsub.get_emulator_endpoint()
	print(f"Pub/Sub emulator running at {endpoint}")
```