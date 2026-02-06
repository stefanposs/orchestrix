
# Lakehouse FastAPI Demo — Enterprise Data Platform

Build an event-sourced, enterprise-grade data platform with dataset lifecycle
management, data contracts, SLA enforcement, pluggable executor backends,
full-pipeline automation, and real-time SSE streaming.

> **Source Code:**
> [`bases/orchestrix/lakehouse_fastapi_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/lakehouse_fastapi_demo)

## Overview

| Capability | Description |
|---|---|
| Dataset Lifecycle | Register, version, deprecate datasets with schema + description |
| Data Contracts | Define quality & privacy rules; approve or decline contracts |
| Batch Lifecycle | Append → Quarantine → Validate → Publish → Consume |
| SLA Enforcement | Freshness & availability SLAs with breach detection |
| Executor Layer | Pluggable backends: LocalPython, BigQuery, Spark, dbt |
| Pipeline Automation | Full ingest → validate → privacy → publish in one call |
| Observability | Platform dashboard with health scores, SLA compliance, execution metrics |
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

### Datasets (`/datasets`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/datasets` | Register a new dataset |
| `GET`  | `/datasets` | List all datasets |
| `GET`  | `/datasets/{name}` | Get dataset details |
| `POST` | `/datasets/{name}/deprecate` | Deprecate a dataset |
| `POST` | `/datasets/{name}/activate-version` | Activate a dataset version |

### Contracts (`/contracts`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/contracts` | Create a data contract |
| `GET`  | `/contracts` | List all contracts |
| `POST` | `/contracts/{id}/approve` | Approve a contract |
| `POST` | `/contracts/{id}/decline` | Decline (deprecate) a contract |

### Batches (`/batches`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/batches/append` | Append a data batch |
| `POST` | `/batches/{id}/quarantine` | Quarantine a batch |
| `POST` | `/batches/{id}/release` | Release from quarantine |
| `POST` | `/batches/{id}/validate` | Run quality check |
| `POST` | `/batches/{id}/privacy-check` | Run privacy check |
| `POST` | `/batches/{id}/publish` | Publish a validated batch |
| `POST` | `/batches/{id}/consume` | Consume a published batch |
| `GET`  | `/batches` | List batches (optional `?dataset=` filter) |
| `GET`  | `/batches/{id}` | Get batch details |

### SLAs (`/slas`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/slas` | Define SLA for a dataset (freshness, availability) |
| `GET`  | `/slas` | List all SLAs (optional `?dataset=` filter) |
| `GET`  | `/slas/{id}` | Get SLA details and breach status |
| `POST` | `/slas/{id}/check` | Run SLA check (pass or breach) |

### Executor (`/executor`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/executor/run` | Run a job on a specific backend |
| `GET`  | `/executor/{id}` | Get execution job status |
| `GET`  | `/executor` | List all execution jobs |

### Pipeline (`/pipeline`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/pipeline/ingest` | Full pipeline: ingest → validate → privacy → publish |

### Events (`/events`)

| Method | Path | Description |
|---|---|---|
| `GET`  | `/events` | Query events (filter by `aggregate_id` or `event_type`) |
| `GET`  | `/events/subscribe` | SSE stream of real-time events |
| `POST` | `/events/replay` | Replay events for a dataset |

### Operations

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe |
| `GET` | `/dashboard` | Platform observability dashboard |


## End-to-End Walkthrough

### 1. Register a Dataset

```bash
curl -X POST http://localhost:8000/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "sales", "schema": {"id": "int", "amount": "float"}, "description": "Sales data"}'
```

### 2. Create a Contract

```bash
curl -X POST http://localhost:8000/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "sales",
    "schema": {"id": "int", "amount": "float"},
    "quality_rules": {"amount": ">0"},
    "privacy_rules": {"id": "mask"}
  }'
```

### 3. Approve the Contract

```bash
curl -X POST "http://localhost:8000/contracts/<contract-id>/approve?approver=data-steward"
```

### 4. Define an SLA

```bash
curl -X POST http://localhost:8000/slas \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "sales",
    "freshness_hours": 24,
    "availability_pct": 99.9,
    "owner": "data-platform-team",
    "consumers": ["analytics", "ml-team"]
  }'
```

### 5. Full Pipeline (one-shot)

```bash
curl -X POST http://localhost:8000/pipeline/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "sales",
    "contract_id": "<contract-id>",
    "file_url": "s3://bucket/sales_2025_01.csv",
    "quality_rules": {"amount": ">0"},
    "privacy_rules": {"id": "mask"}
  }'
# → Returns step-by-step results: ingest → validate → privacy → publish
```

### 6. Or Step-by-Step

```bash
# Append
curl -X POST http://localhost:8000/batches/append \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales", "contract_id": "<contract-id>", "file_url": "s3://bucket/data.csv"}'

# Validate
curl -X POST http://localhost:8000/batches/<batch-id>/validate \
  -H "Content-Type: application/json" \
  -d '{"quality_rules": {"amount": ">0"}}'

# Privacy check
curl -X POST http://localhost:8000/batches/<batch-id>/privacy-check \
  -H "Content-Type: application/json" \
  -d '{"privacy_rules": {"id": "mask"}}'

# Publish
curl -X POST http://localhost:8000/batches/<batch-id>/publish

# Consume
curl -X POST http://localhost:8000/batches/<batch-id>/consume \
  -H "Content-Type: application/json" \
  -d '{"consumer": "analytics-team"}'
```

### 7. Run Executor Job

```bash
curl -X POST http://localhost:8000/executor/run \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "validation",
    "dataset": "sales",
    "batch_id": "<batch-id>",
    "executor_type": "local_python",
    "parameters": {"quality_rules": {"amount": ">0"}}
  }'
```

### 8. Check SLA

```bash
curl -X POST http://localhost:8000/slas/<sla-id>/check \
  -H "Content-Type: application/json" \
  -d '{"freshness_ok": true, "availability_ok": true}'
```

### 9. Platform Dashboard

```bash
curl http://localhost:8000/dashboard
# → Health score, SLA compliance, publish rates, execution metrics per dataset
```

### 10. Stream Events (SSE)

```bash
curl -N http://localhost:8000/events/subscribe
```


## Domain Model

### Aggregates

| Aggregate | Responsibility |
|---|---|
| `DatasetAggregate` | Dataset lifecycle -- register, activate version, deprecate |
| `ContractAggregate` | Contract lifecycle -- create, approve, decline, update |
| `BatchAggregate` | Batch ingestion lifecycle -- append, quarantine, validate, publish |
| `SLAAggregate` | SLA enforcement -- define, check, breach detection |
| `ExecutionJobAggregate` | Executor job lifecycle -- request, complete, fail |
| `AnonymizationJob` | GDPR anonymization -- dry-run, approve, execute, rollback |

### Key Commands

| Command | Description |
|---|---|
| `RegisterDataset` | Register a new dataset with schema |
| `DeprecateDataset` | Mark a dataset as deprecated |
| `ActivateDatasetVersion` | Activate a specific dataset version |
| `CreateContract` | Define a data contract with quality & privacy rules |
| `ApproveContract` | Approve a data contract |
| `DeclineContract` | Decline a data contract |
| `AppendData` | Append a batch to a dataset |
| `QuarantineBatch` | Mark a batch as faulty |
| `ReleaseQuarantine` | Release a batch from quarantine |
| `PublishData` | Publish a validated batch |
| `DefineSLA` | Define freshness + availability SLA for a dataset |
| `CheckSLA` | Trigger an SLA compliance check |
| `RequestExecution` | Submit a job to an executor backend |

### Key Events

| Event | Trigger |
|---|---|
| `DatasetRegistered` | Dataset registered |
| `DatasetDeprecated` | Dataset deprecated |
| `DatasetVersionActivated` | Dataset version activated |
| `DataContractDefined` | Contract created |
| `DataContractApproved` | Contract approved |
| `DataContractDeprecated` | Contract declined |
| `DataAppended` | Batch appended |
| `BatchQuarantined` | Batch quarantined |
| `QualityCheckPassed` | DQ check succeeded |
| `PrivacyCheckPassed` | Privacy check succeeded |
| `DataPublished` | Batch published |
| `SLADefined` | SLA created for a dataset |
| `SLACheckPassed` | SLA check passed |
| `SLABreached` | SLA violated |
| `ExecutionStarted` | Executor job started |
| `ExecutionCompleted` | Executor job completed |
| `ExecutionFailed` | Executor job failed |

### Batch Lifecycle

```
INGESTED --> QUARANTINED --(release)--> INGESTED
INGESTED --> DQ_PASSED --> VALIDATED --> PUBLISHED
INGESTED --> PRIVACY_PASSED --> VALIDATED --> PUBLISHED
```

Both DQ and privacy checks must pass (in any order) before a batch
transitions to `VALIDATED`. Only validated batches can be published.

### Executor Backends

| Backend | Description |
|---|---|
| `local_python` | In-process Python executor (dev/testing) |
| `bigquery` | BigQuery SQL jobs (stub, ready for production impl) |
| `spark` | PySpark / Databricks (stub) |
| `dbt` | dbt model runs (stub) |


## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌───────────────────┐
│ FastAPI App  │---▶│  APIRouters  │---▶│ Aggregate + Repo  │
│  (app.py)   │    │  (entry.py)  │    │  (aggregate.py)   │
└─────────────┘    └──────┬───────┘    └─────────┬─────────┘
                          │                      │
                   ┌──────▼───────┐        ┌─────▼──────┐
                   │  Executor    │        │ EventStore │
                   │  Registry    │        │ (in-memory │
                   │ (executor.py)│        │  default)  │
                   └──────────────┘        └─────┬──────┘
                                                 │
                                          ┌──────▼───────┐
                                          │  SLA Monitor │
                                          │ (projection) │
                                          └──────────────┘
```

### Code Structure

```
bases/orchestrix/lakehouse_fastapi_demo/
├── app.py           # FastAPI application assembly + router mounting
├── entry.py         # Route handlers, SSE notifier, Pydantic I/O models
├── aggregate.py     # DatasetAggregate, ContractAggregate, BatchAggregate,
│                    # SLAAggregate, ExecutionJobAggregate, AnonymizationJob
├── models.py        # Commands, Events, domain value objects
├── executor.py      # Pluggable executor layer (LocalPython, BigQuery, Spark, dbt)
├── sla_monitor.py   # SLA monitoring projection (health scores, breach tracking)
├── engine.py        # Anonymization strategies (mask, hash, pseudonymize, generalize)
├── saga.py          # Anonymization saga (dry-run → approval → execution)
├── gdpr.py          # GDPR compliance (right-to-be-forgotten, access audit)
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
