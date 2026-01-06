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
    """Input model for registering a dataset."""

    name: str
    schema: dict[str, str]


class CreateContractIn(BaseModel):
    """Input model for registering a contract."""

    dataset: str
    retention_days: int


class UploadUrlIn(BaseModel):
    """Input model for requesting an upload URL."""

    filename: str


class AppendBatchIn(BaseModel):
    """Input model for appending a batch."""

    dataset: str
    contract_id: str
    batch_id: str
    file_url: str


class QuarantineBatchIn(BaseModel):
    """Input model for quarantining a batch."""

    batch_id: str
    reason: str


class RunDQIn(BaseModel):
    """Input model for running data quality checks."""

    batch_id: str
    quality_rules: dict[str, str]


class RunPrivacyIn(BaseModel):
    """Input model for running privacy checks."""

    batch_id: str
    privacy_rules: dict[str, str]


class PublishBatchIn(BaseModel):
    """Input model for publishing a batch."""

    batch_id: str


class ConsumeBatchIn(BaseModel):
    """Input model for consuming a batch."""

    batch_id: str
    consumer: str


class ReplayIn(BaseModel):
    """Input model for replaying events for a dataset."""

    dataset: str


print("entry.py loaded")

# --- Routers for process grouping ---
datasets_router = APIRouter(prefix="/datasets", tags=["Datasets"])
contracts_router = APIRouter(prefix="/contracts", tags=["Contracts"])
batches_router = APIRouter(prefix="/batches", tags=["Batches"])
events_router = APIRouter(prefix="/events", tags=["Events"])


# --- Dataset Management ---
@datasets_router.post(
    "/register-dataset",
    summary="Register Dataset",
    description="Register a new dataset with a given name and schema.",
)
async def register_dataset(data: RegisterDatasetIn) -> dict:
    """Register a new dataset with a given name and schema."""
    if data.name in DATASETS:
        raise HTTPException(status_code=400, detail="Dataset already exists")
    DATASETS[data.name] = {"schema": data.schema}
    return {"message": f"Dataset '{data.name}' registered."}


@datasets_router.post(
    "/get-upload-url",
    summary="Get Upload Url",
    description="Get a pre-signed upload URL for a file.",
)
async def get_upload_url(data: UploadUrlIn) -> dict:
    """Get a pre-signed upload URL for a file."""
    url = f"https://fake-bucket.s3.amazonaws.com/{data.filename}"
    UPLOAD_URLS[data.filename] = url
    return {"upload_url": url}


@datasets_router.post(
    "/run-dq", summary="Run Dq", description="Run data quality checks for a batch."
)
async def run_dq(data: RunDQIn) -> dict:
    """Run data quality checks for a batch."""
    return {"message": f"DQ checked for batch '{data.batch_id}'."}


@datasets_router.post(
    "/run-privacy", summary="Run Privacy", description="Run privacy checks for a batch."
)
async def run_privacy(data: RunPrivacyIn) -> dict:
    """Run privacy checks for a batch."""
    return {"message": f"Privacy checked for batch '{data.batch_id}'."}


# --- Contract Management ---
@contracts_router.post(
    "/register-contract",
    summary="Register Contract",
    description="Register a contract for a dataset, specifying retention days.",
)
async def register_contract(data: CreateContractIn) -> dict:
    """Register a contract for a dataset, specifying retention days."""
    if data.dataset not in DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    CONTRACTS[data.dataset] = {"retention_days": data.retention_days}
    return {"message": f"Contract for dataset '{data.dataset}' registered."}


# --- Batch Processing ---
@batches_router.post(
    "/append-batch", summary="Append Batch", description="Append a new batch to a dataset."
)
async def append_batch(data: AppendBatchIn) -> dict:
    """Append a new batch to a dataset."""
    BATCHES[data.batch_id] = {"dataset": data.dataset, "file_url": data.file_url}
    return {"message": f"Batch '{data.batch_id}' appended to dataset '{data.dataset}'."}


@batches_router.post(
    "/quarantine-batch",
    summary="Quarantine Batch",
    description="Quarantine a batch for a given reason.",
)
async def quarantine_batch(data: QuarantineBatchIn) -> dict:
    """Quarantine a batch for a given reason."""
    return {"message": f"Batch '{data.batch_id}' quarantined: {data.reason}"}


@batches_router.post(
    "/publish-batch",
    summary="Publish Batch",
    description="Publish a batch to make it available for consumption.",
)
async def publish_batch(data: PublishBatchIn) -> dict:
    """Publish a batch to make it available for consumption."""
    return {"message": f"Batch '{data.batch_id}' published."}


@batches_router.post(
    "/consume-batch",
    summary="Consume Batch",
    description="Consume a published batch as a consumer.",
)
async def consume_batch(data: ConsumeBatchIn) -> dict:
    """Consume a published batch as a consumer."""
    return {"message": f"Batch '{data.batch_id}' consumed by '{data.consumer}'."}


# --- Event & Replay ---
@events_router.post(
    "/replay-events", summary="Replay Events", description="Replay all events for a given dataset."
)
async def replay_events(data: ReplayIn) -> dict:
    """Replay all events for a given dataset."""
    if data.dataset not in DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": f"Replay for dataset '{data.dataset}' completed."}


@events_router.get(
    "/get-events", summary="Get Events", description="Get a list of events for a batch or dataset."
)
async def get_events(
    batch_id: str = Query(None), dataset: str = Query(None), event_type: str = Query(None)
) -> dict:
    """Get a list of events for a batch or dataset."""
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


router = APIRouter()


@router.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to /docs."""
    return RedirectResponse(url="/docs")
