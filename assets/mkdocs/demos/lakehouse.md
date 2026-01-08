# Lakehouse FastAPI Demo

A self-service, event-sourced data platform demo. This example shows how to build a modular, auditable data lakehouse API using Orchestrix, FastAPI, and event-driven processes.

---

## Core Processes & Events

| Process              | Command                  | Event(s) Produced                | Description                                  |
|----------------------|-------------------------|----------------------------------|----------------------------------------------|
| Register Dataset     | RegisterDataset         | DatasetRegistered                | Register a new dataset with schema           |
| Register Contract    | CreateContract          | DataContractDefined              | Define contract/retention for a dataset      |
| Upload Batch         | AppendData              | DataAppended                     | Upload a data batch (CSV)                    |
| Replay               | RequestReplay           | ReplayRequested, ReplayCompleted | Reprocess all batches for a dataset          |
| Quarantine Batch     | QuarantineBatch         | BatchQuarantined                 | Mark batch as faulty                         |
| Data Quality Check   | RunQualityCheck         | QualityCheckPassed/Failed        | Run DQ checks for a batch                    |
| Privacy Check        | AnonymizeData           | DataAnonymized                   | Run privacy/compliance checks                |
| Publish Batch        | PublishData             | DataPublished                    | Make batch available for consumption         |
| Consume Batch        | GrantConsumption        | ConsumptionGranted               | Grant access to batch (signed URL)           |

---

## End-to-End API Example

### 1. Start the FastAPI server
```bash
uv run main:start
```

### 2. Register a Dataset
```bash
curl -X POST http://localhost:8000/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "sales", "schema": {"id": "int", "amount": "float"}}'
```

### 3. Register a Contract
```bash
curl -X POST http://localhost:8000/contracts \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales", "retention_days": 365}'
```

### 4. Get Signed Upload URL
```bash
curl -X POST http://localhost:8000/upload-url \
  -H "Content-Type: application/json" \
  -d '{"filename": "sales_2024_01.csv"}'
# Response: { "upload_url": "https://..." }
```

### 5. Upload Data as CSV
```bash
echo "id,amount\n1,100.0\n2,200.0" > sales_2024_01.csv
curl -X PUT "<UPLOAD_URL_FROM_STEP_4>" --data-binary @sales_2024_01.csv
```

### 6. Append Batch
```bash
curl -X POST http://localhost:8000/append-batch \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales", "contract_id": "contract1", "batch_id": "batch1", "file_url": "sales_2024_01.csv"}'
```

### 7. (Optional) Quarantine Batch
```bash
curl -X POST http://localhost:8000/quarantine-batch \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch1", "reason": "DQ failed"}'
```

### 8. Run Data Quality Check
```bash
curl -X POST http://localhost:8000/run-dq \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch1", "quality_rules": {"amount": ">0"}}'
```

### 9. Run Privacy Check
```bash
curl -X POST http://localhost:8000/run-privacy \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch1", "privacy_rules": {"id": "mask"}}'
```

### 10. Publish Batch
```bash
curl -X POST http://localhost:8000/publish-batch \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch1"}'
```

### 11. Consume Batch
```bash
curl -X POST http://localhost:8000/consume-batch \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch1", "consumer": "alice"}'
```

### 12. (Optional) Replay
```bash
curl -X POST http://localhost:8000/replay \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales"}'
```

---

## Event-Driven Architecture

- Every command triggers at least one event (event sourcing)
- All events are auditable and reconstruct system state
- Modular: add new checks, events, or processes easily
- Upload/download always via signed URLs (cloud-agnostic)
- Storage backend is pluggable (local, S3, Azure, ...)

---

## Files & Structure

- `models.py`: All commands/events for the process API
- `aggregate.py`: Aggregates for Dataset, Contract, Batch
- `app.py`/`entry.py`: FastAPI app and entrypoint
- `engine.py`, `gdpr.py`: Optional privacy, DQ, compliance logic

---

**Note:** This demo is fully modular, process-driven, and all business logic lives in `bases/`. No Python code in `projects/`.
