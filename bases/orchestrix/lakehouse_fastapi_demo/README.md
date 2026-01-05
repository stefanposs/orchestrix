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

### 2. Register a Dataset
```bash
curl -X POST http://localhost:8000/datasets \

## Process Overview
```

### 3. Register a Contract
```bash
curl -X POST http://localhost:8000/contracts \

1. **Register Dataset** (`POST /datasets`): Create a new dataset with schema.
```

### 4. Get a Signed Upload URL for CSV
```bash
curl -X POST http://localhost:8000/datasets/sales/upload-url \
2. **Register Contract** (`POST /contracts`): Define retention and compliance for a dataset.
3. **Upload Data** (`POST /upload-url`): Get a signed URL for file upload.
# Response: { "url": "https://...signed-upload-url..." }
```

### 5. Upload Data as CSV (to signed URL)
```bash
# Example CSV file:
echo "id,amount\n1,100.0\n2,200.0" > sales_2024_01.csv

# Upload to signed URL (replace <SIGNED_URL> with the value from previous step)
curl -X PUT "<SIGNED_URL>" \
4. **Replay** (`POST /replay`): Trigger a replay of all batches for a dataset.

```

### 6. (Optional) Replay Data Processing
```bash
curl -X POST http://localhost:8000/replay \
### How it works

```

### 7. Consume Data as CSV (Download via signed URL)
```bash
curl -X POST http://localhost:8000/datasets/sales/download-url \
- All business logic is in `bases/orchestrix/lakehouse_demo_fastapi/`.
- The FastAPI app exposes endpoints for all core processes.
# Response: { "url": "https://...signed-download-url..." }

# Download the CSV file
curl -L "<SIGNED_DOWNLOAD_URL>" -o downloaded_sales.csv
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
