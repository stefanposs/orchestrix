from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# --- In-memory stores (for demo only) ---
DATASETS = {}
CONTRACTS = {}
UPLOAD_URLS = {}
BATCHES = {}


# --- API Models (Commands) ---
class RegisterDatasetIn(BaseModel):
    """Register a new dataset."""

    name: str
    schema: dict[str, str]


class CreateContractIn(BaseModel):
    """Create a contract for a dataset."""

    dataset: str
    retention_days: int


class UploadUrlIn(BaseModel):
    """Request a signed upload URL."""

    filename: str


class AppendBatchIn(BaseModel):
    """Append a data batch."""

    dataset: str
    contract_id: str
    batch_id: str
    file_url: str


class QuarantineBatchIn(BaseModel):
    """Quarantine a batch."""

    batch_id: str
    reason: str


class RunDQIn(BaseModel):
    """Run a data quality check."""

    batch_id: str
    quality_rules: dict[str, str]


class RunPrivacyIn(BaseModel):
    """Run a privacy check."""

    batch_id: str
    privacy_rules: dict[str, str]


class PublishBatchIn(BaseModel):
    """Publish a batch."""

    batch_id: str


class ConsumeBatchIn(BaseModel):
    """Consume a batch."""

    batch_id: str
    consumer: str


class ReplayIn(BaseModel):
    """Replay all batches for a dataset."""

    dataset: str


print("entry.py loaded")
# --- FastAPI Router ---
router = APIRouter()


@router.post("/datasets")
async def register_dataset(data: RegisterDatasetIn) -> dict:
    """Register a new dataset."""
    if data.name in DATASETS:
        raise HTTPException(status_code=400, detail="Dataset already exists")
    DATASETS[data.name] = {"schema": data.schema}
    return {"message": f"Dataset '{data.name}' registered."}


@router.post("/contracts")
async def register_contract(data: CreateContractIn) -> dict:
    """Create a contract for a dataset."""
    if data.dataset not in DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    CONTRACTS[data.dataset] = {"retention_days": data.retention_days}
    return {"message": f"Contract for dataset '{data.dataset}' registered."}


@router.post("/upload-url")
async def get_upload_url(data: UploadUrlIn) -> dict:
    """Request a signed upload URL."""
    url = f"https://fake-bucket.s3.amazonaws.com/{data.filename}"
    UPLOAD_URLS[data.filename] = url
    return {"upload_url": url}


@router.post("/append-batch")
async def append_batch(data: AppendBatchIn) -> dict:
    """Append a new data batch to a dataset."""
    BATCHES[data.batch_id] = {"dataset": data.dataset, "file_url": data.file_url}
    return {"message": f"Batch '{data.batch_id}' appended to dataset '{data.dataset}'."}


@router.post("/quarantine-batch")
async def quarantine_batch(data: QuarantineBatchIn) -> dict:
    """Quarantine a batch due to data issues."""
    return {"message": f"Batch '{data.batch_id}' quarantined: {data.reason}"}


@router.post("/run-dq")
async def run_dq(data: RunDQIn) -> dict:
    """Run a data quality check on a batch."""
    return {"message": f"DQ checked for batch '{data.batch_id}'."}


@router.post("/run-privacy")
async def run_privacy(data: RunPrivacyIn) -> dict:
    """Run a privacy/compliance check on a batch."""
    return {"message": f"Privacy checked for batch '{data.batch_id}'."}


@router.post("/publish-batch")
async def publish_batch(data: PublishBatchIn) -> dict:
    """Publish a batch for consumption."""
    return {"message": f"Batch '{data.batch_id}' published."}


@router.post("/consume-batch")
async def consume_batch(data: ConsumeBatchIn) -> dict:
    """Consume a published batch as a consumer."""
    return {"message": f"Batch '{data.batch_id}' consumed by '{data.consumer}'."}


@router.post("/replay")
async def replay_events(data: ReplayIn) -> dict:
    """Replay all batches for a dataset."""
    if data.dataset not in DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": f"Replay for dataset '{data.dataset}' completed."}


# --- Event Query Endpoint ---
@router.get("/events")
async def get_events(
    batch_id: str = Query(None), dataset: str = Query(None), event_type: str = Query(None)
) -> dict:
    """Query events (demo placeholder, returns static example)."""
    # In real system, would query event store
    return {
        "events": [
            {
                "type": event_type or "BatchAppended",
                "batch_id": batch_id or "batch1",
                "dataset": dataset or "sales",
            },
            {"type": "DQChecked", "batch_id": batch_id or "batch1"},
        ]
    }


# Root redirect to Swagger UI
@router.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root URL to Swagger UI."""
    return RedirectResponse(url="/docs")
