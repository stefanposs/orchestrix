# Lakehouse FastAPI Demo

Event-sourced self-service lakehouse platform built with **Orchestrix** aggregates, `AggregateRepository`, and `InMemoryEventStore`.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  FastAPI     │────▶│  Aggregates  │────▶│  EventStore    │
│  Endpoints   │     │  (DDD)       │     │  (in-memory)   │
└─────────────┘     └──────────────┘     └────────────────┘
      │                    │
      │  Pydantic          │  _apply_event()
      │  Request/Response  │  _when_*() handlers
      ▼                    ▼
  Typed JSON          Domain Events
```

**Core Concepts:**
- **Dataset** — Registered data object with schema and description
- **Contract** — Data contract with schema, privacy rules, and quality rules
- **Batch** — Single data delivery with full lifecycle (see below)

---

## Batch Lifecycle (State Machine)

A batch goes through the following states:

```
                    ┌──────────────────────────┐
                    │                          │
                    ▼                          │
INGESTED ──┬──▶ QUARANTINED ──▶ (release) ────┘
           │
           ├──▶ DQ Check   ──┐
           │                  ├──▶ VALIDATED ──▶ PUBLISHED
           └──▶ Privacy Check ┘
```

| Status | Meaning |
|--------|---------|
| **INGESTED** | Batch was successfully appended — ready for validation |
| **QUARANTINED** | Batch was isolated (e.g., faulty data). Cannot be published until released |
| **VALIDATED** | Both checks (DQ + Privacy) passed — ready for publish |
| **PUBLISHED** | Batch is released and available for consumers |

### Endpoints

| Endpoint | Action | Purpose |
|----------|--------|---------|
| `POST /batches/append` | Append new data delivery | Each CSV/Parquet file is registered as a batch |
| `POST /batches/{id}/quarantine` | Isolate batch | When DQ checks fail or anomalies are detected |
| `POST /batches/{id}/release` | Release from quarantine | After manual review/fix: batch may be validated again |
| `POST /batches/{id}/validate` | Run data quality check | Validates quality rules (e.g., `amount > 0`, `id not null`) |
| `POST /batches/{id}/privacy-check` | Run privacy/compliance check | Validates GDPR rules (e.g., PII masking, hashing) |
| `POST /batches/{id}/publish` | Publish batch | Only after validation: batch released for consumers |
| `POST /batches/{id}/consume` | Consume batch | Consumer receives signed download URL. Published batches only |

### Typical Happy Path

```
1. POST /datasets          → Register dataset
2. POST /contracts         → Create data contract
3. POST /batches/append    → Append data         → status: ingested
4. POST /batches/{id}/validate      → DQ check   → dq_passed: true
5. POST /batches/{id}/privacy-check → Privacy     → status: validated
6. POST /batches/{id}/publish       → Publish     → status: published
7. POST /batches/{id}/consume       → Download    → ✅
```

### Quarantine Scenario

```
1. POST /batches/append              → status: ingested
2. POST /batches/{id}/quarantine     → status: quarantined (blocked!)
3. POST /batches/{id}/release        → status: ingested (unblocked)
4. POST /batches/{id}/validate       → DQ check again
5. ...continue with happy path
```

---

## All Endpoints

### Datasets
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/datasets` | Register dataset (name, schema, description) |
| `GET` | `/datasets` | List all datasets |
| `GET` | `/datasets/{name}` | Get single dataset |

### Contracts
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/contracts` | Create data contract (schema, privacy/quality rules) |
| `GET` | `/contracts` | List all contracts |

### Batches
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/batches/append` | Append data batch |
| `GET` | `/batches` | List all batches (optional `?dataset=name`) |
| `GET` | `/batches/{id}` | Get single batch |
| `POST` | `/batches/{id}/quarantine` | Isolate batch |
| `POST` | `/batches/{id}/release` | Release from quarantine |
| `POST` | `/batches/{id}/validate` | Run DQ check |
| `POST` | `/batches/{id}/privacy-check` | Run privacy check |
| `POST` | `/batches/{id}/publish` | Publish batch |
| `POST` | `/batches/{id}/consume` | Consume batch (download URL) |

### Events
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events/replay` | Replay events for a dataset |
| `GET` | `/events` | Query event log (filter: `aggregate_id`, `event_type`) |

### Operations
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe |

---

## Running

```bash
uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app --reload
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Tech Stack

- **Orchestrix** — AggregateRoot, AggregateRepository, InMemoryEventStore
- **FastAPI** + Pydantic v2 — Typed REST API
- **Event Sourcing** — All state changes stored as domain events
- **DDD** — Aggregates with lifecycle guards and state machine
