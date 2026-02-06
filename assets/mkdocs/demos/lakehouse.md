
# Lakehouse FastAPI Demo — Self-Service Data Platform

Build an event-sourced, self-service data platform with full batch lifecycle,
data contracts, quality gates, privacy checks, and real-time SSE streaming.

> **Source Code:**
> [`bases/orchestrix/lakehouse_fastapi_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/lakehouse_fastapi_demo)

## Overview

| Capability | Description |
|---|---|
| Dataset Registry | Register datasets with schema + description |
| Data Contracts | Define quality & privacy rules per dataset |
| Batch Lifecycle | Append → Quarantine → Validate → Publish → Consume |
| Quality Gates | DQ + privacy checks; both must pass before publishing |
| GDPR Compliance | Anonymization engine with dry-run, approval, rollback |
| SSE Streaming | Real-time CloudEvents via Server-Sent Events |
| Swagger UI | Interactive docs at `/docs` |

## Quick Start

```bash
uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app --reload
# Open http://localhost:8000/docs
```

## REST API Endpoints

### Datasets (`/api/v1/datasets`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/datasets` | Register a new dataset |
| `GET`  | `/api/v1/datasets` | List all datasets |
| `GET`  | `/api/v1/datasets/{name}` | Get dataset details |

### Contracts (`/api/v1/contracts`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/contracts` | Create a data contract |
| `GET`  | `/api/v1/contracts` | List all contracts |

### Batches (`/api/v1/batches`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/batches/append` | Append a data batch |
| `POST` | `/api/v1/batches/{id}/quarantine` | Quarantine a batch |
| `POST` | `/api/v1/batches/{id}/release` | Release from quarantine |
| `POST` | `/api/v1/batches/{id}/validate` | Run quality check |
| `POST` | `/api/v1/batches/{id}/privacy-check` | Run privacy check |
| `POST` | `/api/v1/batches/{id}/publish` | Publish a validated batch |
| `POST` | `/api/v1/batches/{id}/consume` | Consume a published batch |
| `GET`  | `/api/v1/batches` | List batches (optional `?dataset=` filter) |
| `GET`  | `/api/v1/batches/{id}` | Get batch details |

### Events (`/api/v1/events`)

| Method | Path | Description |
|---|---|---|
| `GET`  | `/api/v1/events` | Query events (filter by `aggregate_id` or `event_type`) |
| `GET`  | `/api/v1/events/stream` | SSE stream of real-time events |
| `POST` | `/api/v1/events/replay` | Replay events for a dataset |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe |


## End-to-End Walkthrough

### 1. Register a Dataset

```bash
curl -X POST http://localhost:8000/api/v1/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "sales", "schema_def": {"id": "int", "amount": "float"}, "description": "Sales data"}'
```

### 2. Create a Contract

```bash
curl -X POST http://localhost:8000/api/v1/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "sales",
    "schema_def": {"id": "int", "amount": "float"},
    "quality_rules": {"amount": ">0"},
    "privacy_rules": {"id": "mask"}
  }'
```

### 3. Append a Batch

```bash
curl -X POST http://localhost:8000/api/v1/batches/append \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "sales",
    "contract_id": "<contract-id-from-step-2>",
    "file_url": "s3://bucket/sales_2025_01.csv"
  }'
```

### 4. Run Quality Check

```bash
curl -X POST http://localhost:8000/api/v1/batches/<batch-id>/validate \
  -H "Content-Type: application/json" \
  -d '{"quality_rules": {"amount": ">0"}}'
```

### 5. Run Privacy Check

```bash
curl -X POST http://localhost:8000/api/v1/batches/<batch-id>/privacy-check \
  -H "Content-Type: application/json" \
  -d '{"privacy_rules": {"id": "mask"}}'
```

### 6. Publish

```bash
curl -X POST http://localhost:8000/api/v1/batches/<batch-id>/publish
```

### 7. Consume

```bash
curl -X POST http://localhost:8000/api/v1/batches/<batch-id>/consume \
  -H "Content-Type: application/json" \
  -d '{"consumer": "analytics-team"}'
# → Returns a signed download URL
```

### 8. Stream Events (SSE)

```bash
curl -N http://localhost:8000/api/v1/events/stream
```


## Domain Model

### Aggregates

| Aggregate | Responsibility |
|---|---|
| `DatasetAggregate` | Dataset lifecycle — register, activate version, deprecate |
| `ContractAggregate` | Contract lifecycle — create, approve, decline, update |
| `BatchAggregate` | Batch ingestion lifecycle — append, quarantine, validate, publish |
| `AnonymizationJob` | GDPR anonymization — dry-run, approve, execute, rollback |

### Key Commands

| Command | Description |
|---|---|
| `RegisterDataset` | Register a new dataset with schema |
| `CreateContract` | Define a data contract with quality & privacy rules |
| `AppendData` | Append a batch to a dataset |
| `QuarantineBatch` | Mark a batch as faulty |
| `ReleaseQuarantine` | Release a batch from quarantine |
| `RunQualityCheck` | Run DQ rules against a batch |
| `PublishData` | Publish a validated batch |
| `GrantConsumption` | Grant signed-URL access to a batch |

### Key Events

| Event | Trigger |
|---|---|
| `DatasetRegistered` | Dataset registered |
| `DataContractDefined` | Contract created |
| `DataAppended` | Batch appended |
| `BatchQuarantined` | Batch quarantined |
| `QualityCheckPassed` | DQ check succeeded |
| `PrivacyCheckPassed` | Privacy check succeeded |
| `DataPublished` | Batch published |
| `ConsumptionGranted` | Download URL issued |

### Batch Lifecycle

```
INGESTED ──→ QUARANTINED ──(release)──→ INGESTED
INGESTED ──→ DQ_PASSED ──→ VALIDATED ──→ PUBLISHED
INGESTED ──→ PRIVACY_PASSED ──→ VALIDATED ──→ PUBLISHED
```

Both DQ and privacy checks must pass (in any order) before a batch
transitions to `VALIDATED`. Only validated batches can be published.


## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌───────────────────┐
│ FastAPI App  │───▶│  APIRouters  │───▶│ Aggregate + Repo  │
│  (app.py)   │    │  (entry.py)  │    │  (aggregate.py)   │
└─────────────┘    └──────┬───────┘    └─────────┬─────────┘
                          │                      │
                    ┌─────▼──────┐         ┌─────▼──────┐
                    │ SSE Stream │         │ EventStore │
                    │ /events/   │         │ (in-memory │
                    │   stream   │         │  default)  │
                    └────────────┘         └────────────┘
```

### Code Structure

```
bases/orchestrix/lakehouse_fastapi_demo/
├── app.py          # FastAPI application assembly + router mounting
├── entry.py        # Route handlers, SSE notifier, Pydantic I/O models
├── aggregate.py    # DatasetAggregate, ContractAggregate, BatchAggregate, AnonymizationJob
├── models.py       # Commands, Events, domain value objects
├── engine.py       # Anonymization strategies (mask, hash, pseudonymize, generalize)
├── saga.py         # Anonymization saga (dry-run → approval → execution)
├── gdpr.py         # GDPR compliance (right-to-be-forgotten, access audit)
└── README.md
```

## GDPR & Anonymization

The demo includes a full anonymization pipeline:

1. **`AnonymizationJob`** aggregate tracks job lifecycle
2. **Strategies** in `engine.py`: masking, SHA-256 hashing, pseudonymization, generalization
3. **Saga** in `saga.py`: dry-run → human approval → column-by-column execution → rollback on failure
4. **GDPR helpers** in `gdpr.py`: right-to-be-forgotten, data access audit trail


## Related

- [Banking Demo](banking.md) — Saga pattern for money transfers
- [E-Commerce Demo](ecommerce.md) — Multi-aggregate order processing
- [Notifications Demo](notifications.md) — Retry logic and dead letter queues
