
# Lakehouse FastAPI Demo – A Modern Data Platform Story

Imagine you are a data engineer in a company that needs to process, validate, and audit large volumes of business data every day. You want a platform that empowers teams to register datasets, upload data, run compliance checks, and consume results—all with full transparency and modularity.

This demo shows how to build a self-service, event-sourced lakehouse API using Orchestrix and FastAPI. Every process is modular, every action is auditable, and the architecture is cloud-agnostic.


## Why Lakehouse? Why Event Sourcing?



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


## Architecture Highlights




## Code Structure & Process Flow

**Modular Design:**

**Typical Process Flow:**
1. A user sends an HTTP request (e.g., POST /datasets).
2. The handler receives the request and creates a command (e.g., RegisterDataset).
3. The aggregate processes the command, applies business rules, and emits an event (e.g., DatasetRegistered).
4. The event is stored (event sourcing) and can trigger further processes (e.g., DQ, privacy checks).
5. Every step is modular and easily extensible.

**Event-Driven & Auditable:**

**Entrypoint:**

**Extensibility:**


**Note:** All business logic lives in `bases/`. No Python code in `projects/`. This demo is modular, process-driven, and ready for extension.
