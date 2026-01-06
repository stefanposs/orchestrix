# 🏗 Lakehouse Fastapi Demo 

**Self-Service Lakehouse Plattform – Demo-Base**


## Features & Processes
- Dataset and contract registration (RegisterDataset, CreateContract)
- Append-only ingestion, replay, quarantine, DQ, privacy, publish, consumption
- Event sourcing: every step emits events, full auditability
- Modular: Aggregates for Dataset, Contract, Batch
- FastAPI entrypoints for all core processes


## Architecture
- **models.py**: Commands & events for all processes
- **aggregate.py**: Aggregates (Dataset, Contract, Batch)
- **handlers.py**: API handlers (process-driven)
- **engine.py**: (optional) Privacy, DQ, storage strategies


## API Quickstart

Start the FastAPI server:
```bash
uv run main:start
```

Example requests:

## API Quickstart & End-to-End Example

### 1. Start the FastAPI server
```bash
uv run main:start
```

---


## End-to-End Process Example (API Calls)

### 1. Register Dataset
```bash
curl -X POST http://localhost:8000/datasets \
	-H "Content-Type: application/json" \
	-d '{"name": "sales", "schema": {"id": "int", "amount": "float"}}'
```

### 2. Register Contract
```bash
curl -X POST http://localhost:8000/contracts \
	-H "Content-Type: application/json" \
	-d '{"dataset": "sales", "retention_days": 365}'
```

### 3. Get Signed Upload URL
```bash
curl -X POST http://localhost:8000/upload-url \
	-H "Content-Type: application/json" \
	-d '{"filename": "sales_2024_01.csv"}'
# Response: { "upload_url": "https://..." }
```

### 4. Upload Data as CSV (to signed URL)
```bash
echo "id,amount\n1,100.0\n2,200.0" > sales_2024_01.csv
curl -X PUT "<UPLOAD_URL_FROM_STEP_3>" --data-binary @sales_2024_01.csv
```

### 5. Append Batch
```bash
curl -X POST http://localhost:8000/append-batch \
	-H "Content-Type: application/json" \
	-d '{"dataset": "sales", "contract_id": "contract1", "batch_id": "batch1", "file_url": "sales_2024_01.csv"}'
```

### 6. (Optional) Quarantine Batch
```bash
curl -X POST http://localhost:8000/quarantine-batch \
	-H "Content-Type: application/json" \
	-d '{"batch_id": "batch1", "reason": "DQ failed"}'
```

### 7. Run Data Quality Check
```bash
curl -X POST http://localhost:8000/run-dq \
	-H "Content-Type: application/json" \
	-d '{"batch_id": "batch1", "quality_rules": {"amount": ">0"}}'
```

### 8. Run Privacy Check
```bash
curl -X POST http://localhost:8000/run-privacy \
	-H "Content-Type: application/json" \
	-d '{"batch_id": "batch1", "privacy_rules": {"id": "mask"}}'
```

### 9. Publish Batch
```bash
curl -X POST http://localhost:8000/publish-batch \
	-H "Content-Type: application/json" \
	-d '{"batch_id": "batch1"}'
```

### 10. Consume Batch
```bash
curl -X POST http://localhost:8000/consume-batch \
	-H "Content-Type: application/json" \
	-d '{"batch_id": "batch1", "consumer": "alice"}'
```

### 11. (Optional) Replay
```bash
curl -X POST http://localhost:8000/replay \
	-H "Content-Type: application/json" \
	-d '{"dataset": "sales"}'
```

---


**Hinweis zur Entkopplung & Erweiterbarkeit:**

- Upload und Download erfolgen immer über signierte URLs. Die API gibt nur die URLs aus, der eigentliche Datentransfer läuft technologieunabhängig über HTTP PUT/GET.
- Die aktuelle Demo nutzt ein lokales Verzeichnis als Storage-Backend (LocalFile). Die Architektur ist aber so entworfen, dass du mit minimalem Aufwand auf Azure Blob Storage, S3 oder GCS umstellen kannst – einfach durch Austausch der Storage-Komponente.
- So können beliebige Tools, Frameworks oder Plattformen Daten anliefern und konsumieren – ohne direkte Kopplung an das Backend oder eine bestimmte Cloud.
- Kein Python-Code in `projects/`, nur Packaging und Startskripte.
- Optional: `engine.py`, `gdpr.py` bieten erweiterte Privacy- und Compliance-Features für Demo-Zwecke.

---
**Note:** This base is modular, process-driven, and optimized for demo/presentation. All logic is in bases/, no Python logic in projects/.
