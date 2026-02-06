"""Lakehouse Demo API — FastAPI application assembly."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .entry import (
    DomainError,
    batches_router,
    contracts_router,
    datasets_router,
    domain_error_handler,
    events_router,
    health_router,
    router,
)

tags_metadata = [
    {"name": "Datasets", "description": "Register and manage datasets (schema, owner, lifecycle)."},
    {
        "name": "Contracts",
        "description": "Define and manage data contracts (schema, privacy, quality rules).",
    },
    {
        "name": "Batches",
        "description": "Ingest data, validate, quarantine, publish and consume batches.",
    },
    {
        "name": "Events",
        "description": (
            "Query the event log, replay events to rebuild state, "
            "and subscribe via HTTP long-poll for near real-time updates "
            "(enterprise-friendly WebSocket alternative)."
        ),
    },
    {"name": "Operations", "description": "Liveness and readiness probes for orchestration."},
]

app: FastAPI = FastAPI(
    title="Lakehouse Demo API",
    description=(
        "Self-Service Lakehouse Platform — Event-Sourced data management with "
        "dataset registration, data contracts, append-only ingestion, "
        "quality/privacy checks, and full audit trail."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
)

# --- CORS (allows Swagger UI & browser clients) ---
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception handlers ---
app.add_exception_handler(DomainError, domain_error_handler)

# --- Routers ---
app.include_router(datasets_router)
app.include_router(contracts_router)
app.include_router(batches_router)
app.include_router(events_router)
app.include_router(health_router)
app.include_router(router)
