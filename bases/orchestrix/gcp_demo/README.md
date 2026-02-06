# GCP Demo

Google Cloud Platform integration demo — event stores backed by Cloud SQL and BigQuery.

## What It Demonstrates
- **GCP Cloud SQL EventStore**: Append/load events using managed PostgreSQL
- **GCP BigQuery EventStore**: Append/load events using BigQuery for analytics-scale storage
- **Pub/Sub Integration**: Event distribution via Google Cloud Pub/Sub

## Running

Requires GCP credentials and project configuration:

```bash
uv run python -m bases.orchestrix.gcp_demo.main
```

## Key Files
| File | Purpose |
|------|---------|
| `main.py` | Cloud SQL and BigQuery event store demo |
| `pubsub_demo.py` | Pub/Sub message distribution |

## Prerequisites
- GCP project with Cloud SQL, BigQuery, and Pub/Sub enabled
- Application Default Credentials configured (`gcloud auth application-default login`)
