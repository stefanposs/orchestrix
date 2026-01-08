
# Lakehouse FastAPI Demo – A Modern Data Platform Story

Imagine you are a data engineer in a company that needs to process, validate, and audit large volumes of business data every day. You want a platform that empowers teams to register datasets, upload data, run compliance checks, and consume results—all with full transparency and modularity.

This demo shows how to build a self-service, event-sourced lakehouse API using Orchestrix and FastAPI. Every process is modular, every action is auditable, and the architecture is cloud-agnostic.

---

## Why Lakehouse? Why Event Sourcing?

- **Self-Service:** Business teams can register datasets, upload batches, and consume data without IT bottlenecks.
- **Auditability:** Every step emits events, so you can reconstruct the entire system state at any time.
- **Modularity:** Add new checks, processes, or storage backends with minimal effort.
- **Cloud-Agnostic:** Upload/download always via signed URLs—works with local, S3, Azure, GCS, etc.

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

## End-to-End API Story

1. **Start the FastAPI server**
    ```bash
    uv run main:start
    ```

2. **Register a Dataset**
    ```bash
    curl -X POST http://localhost:8000/datasets \
      -H "Content-Type: application/json" \
      -d '{"name": "sales", "schema": {"id": "int", "amount": "float"}}'
    ```

3. **Register a Contract**
    ```bash
    curl -X POST http://localhost:8000/contracts \
      -H "Content-Type: application/json" \
      -d '{"dataset": "sales", "retention_days": 365}'
    ```

4. **Get Signed Upload URL**
    ```bash
    curl -X POST http://localhost:8000/upload-url \
      -H "Content-Type: application/json" \
      -d '{"filename": "sales_2024_01.csv"}'
    # Response: { "upload_url": "https://..." }
    ```

5. **Upload Data as CSV**
    ```bash
    echo "id,amount\n1,100.0\n2,200.0" > sales_2024_01.csv
    curl -X PUT "<UPLOAD_URL_FROM_STEP_4>" --data-binary @sales_2024_01.csv
    ```

6. **Append Batch**
    ```bash
    curl -X POST http://localhost:8000/append-batch \
      -H "Content-Type: application/json" \
      -d '{"dataset": "sales", "contract_id": "contract1", "batch_id": "batch1", "file_url": "sales_2024_01.csv"}'
    ```

7. **Quarantine Batch (optional)**
    ```bash
    curl -X POST http://localhost:8000/quarantine-batch \
      -H "Content-Type: application/json" \
      -d '{"batch_id": "batch1", "reason": "DQ failed"}'
    ```

8. **Run Data Quality Check**
    ```bash
    curl -X POST http://localhost:8000/run-dq \
      -H "Content-Type: application/json" \
      -d '{"batch_id": "batch1", "quality_rules": {"amount": ">0"}}'
    ```

9. **Run Privacy Check**
    ```bash
    curl -X POST http://localhost:8000/run-privacy \
      -H "Content-Type: application/json" \
      -d '{"batch_id": "batch1", "privacy_rules": {"id": "mask"}}'
    ```

10. **Publish Batch**
    ```bash
    curl -X POST http://localhost:8000/publish-batch \
      -H "Content-Type: application/json" \
      -d '{"batch_id": "batch1"}'
    ```

11. **Consume Batch**
    ```bash
    curl -X POST http://localhost:8000/consume-batch \
      -H "Content-Type: application/json" \
      -d '{"batch_id": "batch1", "consumer": "alice"}'
    ```

12. **Replay (optional)**
    ```bash
    curl -X POST http://localhost:8000/replay \
      -H "Content-Type: application/json" \
      -d '{"dataset": "sales"}'
    ```

---

## Architecture Highlights

- **Event Sourcing:** Every state change is an event. Full audit trail and system reconstruction.
- **Aggregates:** Datasets, contracts, and batches are modeled as aggregates.
- **Process API:** Each endpoint represents a business process.
- **Pluggable Storage:** Easily switch between local, S3, Azure, etc.
- **Signed URLs:** Secure, cloud-agnostic data transfer.

---


## Code Structure & Process Flow

**Modular Design:**
- `models.py`: Defines all commands (e.g., RegisterDataset) and events (e.g., DatasetRegistered) as dataclasses.
- `aggregate.py`: Contains aggregates for Dataset, Contract, and Batch. Manages business logic and state.
- `handlers.py`: Implements API endpoints and process logic. Each endpoint triggers the appropriate command/event.
- `engine.py`, `gdpr.py`: Optional modules for advanced features like data quality, privacy, or compliance.

**Typical Process Flow:**
1. A user sends an HTTP request (e.g., POST /datasets).
2. The handler receives the request and creates a command (e.g., RegisterDataset).
3. The aggregate processes the command, applies business rules, and emits an event (e.g., DatasetRegistered).
4. The event is stored (event sourcing) and can trigger further processes (e.g., DQ, privacy checks).
5. Every step is modular and easily extensible.

**Event-Driven & Auditable:**
- Every API call triggers at least one event.
- All events are stored and can be used to reconstruct system state.
- The architecture allows easy addition of new processes, checks, or storage backends.

**Entrypoint:**
- The FastAPI app (`app.py` or `entry.py`) starts the server and registers all endpoints.
- All business logic is in `bases/`, no Python code in `projects/`.

**Extensibility:**
- New processes (e.g., checks, event types) can be added as new commands/events and handlers.
- The storage backend is pluggable: local, S3, Azure, GCS—just swap the storage component.

---

**Note:** All business logic lives in `bases/`. No Python code in `projects/`. This demo is modular, process-driven, and ready for extension.
