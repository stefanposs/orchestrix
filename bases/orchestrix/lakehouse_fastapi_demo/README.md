# Lakehouse FastAPI Demo

**Enterprise Lakehouse Platform -- Event-Sourced Data Management**


## Features & Processes
- Dataset registration with schema, versioning, lifecycle (deprecation)
- Data contracts with schema, privacy rules, quality rules, approve/decline
- Append-only data ingestion with auto-generated batch IDs
- Quality checks, privacy checks, quarantine, publish, consume
- SLA enforcement: freshness & availability thresholds with breach detection
- Pluggable executor layer: LocalPython, BigQuery, Spark, dbt backends
- Full pipeline automation: ingest -> validate -> privacy -> publish in one call
- Observability dashboard: health scores, SLA compliance, execution metrics
- Event sourcing: every step emits events, full audit trail via `/events`
- Modular aggregates: Dataset, Contract, Batch, SLA, ExecutionJob
- FastAPI with Pydantic models, RESTful routing, SSE streaming


## Architecture
- **models.py**: Commands & Events for all processes
- **aggregate.py**: Aggregates (Dataset, Contract, Batch, SLA, ExecutionJob, AnonymizationJob)
- **entry.py**: FastAPI endpoints -- wired to Aggregates via Commands -> Events
- **executor.py**: Pluggable executor layer (LocalPython, BigQuery, Spark, dbt)
- **sla_monitor.py**: SLA monitoring projection (health scores, breach tracking)
- **engine.py**: Anonymization strategies (masking, hashing, pseudonymization)
- **saga.py**: Anonymization saga (dry-run -> approval -> execution -> rollback)
- **gdpr.py**: GDPR compliance demo (data lake, deletion requests, audit)
- **app.py**: FastAPI app setup with tagged routers


## Quick Start

```bash
uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## End-to-End Example (curl)

### 1. Register Dataset
```bash
curl -X POST http://localhost:8000/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "sales", "schema": {"id": "int", "amount": "float"}, "description": "Daily sales"}'
```

### 2. Create Contract
```bash
curl -X POST http://localhost:8000/contracts \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales", "retention_days": 365, "schema": {"id": "int", "amount": "float"}}'
```

### 3. Append Data
```bash
curl -X POST http://localhost:8000/batches/append \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales", "contract_id": "contract-a1b2c3d4", "file_url": "s3://bucket/sales_2024.csv"}'
```

### 4. Run Quality Check
```bash
curl -X POST http://localhost:8000/batches/{batch_id}/validate \
  -H "Content-Type: application/json" \
  -d '{"quality_rules": {"amount": ">0", "id": "not_null"}}'
```

### 5. Publish & Consume
```bash
curl -X POST http://localhost:8000/batches/{batch_id}/publish
curl -X POST http://localhost:8000/batches/{batch_id}/consume \
  -H "Content-Type: application/json" \
  -d '{"consumer": "analytics-team"}'
```

---

## Design Principles

- **RESTful**: Resource-oriented URLs (`POST /datasets`, `POST /slas/{id}/check`)
- **Event Sourced**: Every command emits events, all queryable via `/events`
- **Aggregate-wired**: Endpoints use domain aggregates, not plain dicts
- **Self-Service**: Upload/download via signed URLs, technology-agnostic
- **Pluggable**: Executor backends swappable (LocalPython -> BigQuery -> Spark -> dbt)
- **Observable**: Platform dashboard with health scores, SLA compliance, metrics
- **Extensible**: Storage backend swappable (Local -> S3 -> Azure Blob -> GCS)

---

## Advanced Features

- **executor.py**: Pluggable multi-backend executor (LocalPython, BigQuery, Spark, dbt)
- **sla_monitor.py**: Event-driven SLA monitoring projection (breach tracking, health scores)
- **engine.py**: Anonymization engine (masking, hashing, pseudonymization, generalization)
- **saga.py**: Multi-step anonymization workflow with dry-run, approval, rollback
- **gdpr.py**: GDPR compliance demo (data lake, right-to-be-forgotten, access audit)

---
**Note:** This base is modular, process-driven, and event-sourced. All logic is in `bases/`, no Python logic in `projects/`.
