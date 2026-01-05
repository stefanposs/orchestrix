from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# --- API Models ---
class DatasetIn(BaseModel):
    """Input model for dataset registration."""

    name: str
    schema: dict[str, str]


class ContractIn(BaseModel):
    """Input model for contract registration."""

    dataset: str
    retention_days: int


class UploadUrlIn(BaseModel):
    """Input model for requesting a signed upload URL."""

    filename: str


class ReplayIn(BaseModel):
    """Input model for replay request."""

    dataset: str


# --- In-memory demo stores ---
DATASETS = {}
CONTRACTS = {}
UPLOAD_URLS = {}

# --- FastAPI Router ---


def get_router() -> APIRouter:
    """Create and return the FastAPI router for the Lakehouse API."""
    router = APIRouter()

    @router.post("/datasets")
    async def register_dataset(data: DatasetIn) -> dict:
        if data.name in DATASETS:
            raise HTTPException(status_code=400, detail="Dataset already exists")
        DATASETS[data.name] = {"schema": data.schema}
        return {"message": f"Dataset '{data.name}' registered."}

    @router.post("/contracts")
    async def register_contract(data: ContractIn) -> dict:
        if data.dataset not in DATASETS:
            raise HTTPException(status_code=404, detail="Dataset not found")
        CONTRACTS[data.dataset] = {"retention_days": data.retention_days}
        return {"message": f"Contract for dataset '{data.dataset}' registered."}

    @router.post("/upload-url")
    async def get_upload_url(data: UploadUrlIn) -> dict:
        # Demo: generate a fake upload URL
        url = f"https://fake-bucket.s3.amazonaws.com/{data.filename}"
        UPLOAD_URLS[data.filename] = url
        return {"upload_url": url}

    @router.post("/replay")
    async def replay_events(data: ReplayIn) -> dict:
        # Demo: just acknowledge replay
        if data.dataset not in DATASETS:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return {"message": f"Replay for dataset '{data.dataset}' completed."}

    return router
