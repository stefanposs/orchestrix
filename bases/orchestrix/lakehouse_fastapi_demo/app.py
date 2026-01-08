from fastapi import FastAPI
from .entry import datasets_router, contracts_router, batches_router, events_router, router

tags_metadata = [
    {"name": "Datasets", "description": "Register and manage datasets."},
    {"name": "Contracts", "description": "Register and manage contracts for datasets."},
    {"name": "Batches", "description": "Append, quarantine, publish, and consume batches."},
    {"name": "Events", "description": "Replay and get events for batches and datasets."},
]

app: FastAPI = FastAPI(
    title="Lakehouse Demo API",
    servers=[{"url": "http://0.0.0.0:8000", "description": "Default local dev server"}],
    openapi_tags=tags_metadata,
)
app.include_router(datasets_router)
app.include_router(contracts_router)
app.include_router(batches_router)
app.include_router(events_router)
app.include_router(router)
