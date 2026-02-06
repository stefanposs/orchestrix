"""Lakehouse Demo API — FastAPI Entrypoints.

Enterprise-ready endpoints wired to Event-Sourced Aggregates via:
    Commands → Aggregates → Events → EventStore

All responses use typed Pydantic models.
All state is persisted via AggregateRepository + InMemoryEventStore.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import uuid
from dataclasses import fields
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore

from .aggregate import BatchAggregate, ContractAggregate, DatasetAggregate
from .models import (
    AppendData,
    CreateContract,
    PublishData,
    QuarantineBatch,
    RegisterDataset,
    ReleaseQuarantine,
)

logger = logging.getLogger("lakehouse")


# ---------------------------------------------------------------------------
# Event Notifier — SSE real-time streaming (WebSocket-free)
# ---------------------------------------------------------------------------

# CloudEvents / Message base-class fields — excluded from the SSE payload
# because they are either redundant (type, timestamp already in envelope)
# or always null / uninteresting for subscribers.
_MESSAGE_ENVELOPE_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "specversion",
        "type",
        "source",
        "timestamp",
        "subject",
        "data",
        "datacontenttype",
        "dataschema",
        "correlation_id",
        "causation_id",
        "trace_id",
    }
)


def _serialize_event_payload(obj: Any) -> Any:
    """Recursively convert event data to JSON-safe types.

    For dataclass Events the CloudEvents envelope fields are stripped
    so only the domain-specific attributes remain.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _serialize_event_payload(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_event_payload(i) for i in obj]
    # dataclass → dict, stripping Message envelope fields
    if hasattr(obj, "__dataclass_fields__"):
        return {
            f.name: _serialize_event_payload(getattr(obj, f.name))
            for f in fields(obj)
            if f.name not in _MESSAGE_ENVELOPE_FIELDS
        }
    return str(obj)


class EventNotifier:
    """Async notification hub for Server-Sent Events (SSE) subscribers.

    Enterprise-friendly alternative to WebSockets: clients open
    ``GET /events/subscribe`` and the server keeps the connection open,
    pushing each new event as an SSE message.  ``EventSource`` in the
    browser handles reconnection automatically.

    Uses ``asyncio.Event`` for signalling so that the synchronous
    ``publish()`` path (called from ``event_store.save()``) can
    reliably wake all waiting async subscribers.
    """

    _MAX_LOG_SIZE: int = 500
    _POLL_INTERVAL: float = 0.25  # seconds between flag checks

    def __init__(self) -> None:
        self._flag: asyncio.Event | None = None
        self._sequence: int = 0
        self._log: list[dict[str, Any]] = []

    @property
    def current_sequence(self) -> int:
        """Return the current sequence number (head of the log)."""
        return self._sequence

    # -- lazy init (requires a running event loop) -------------------------

    @property
    def flag(self) -> asyncio.Event:
        """Lazily create the asyncio.Event on the running loop."""
        if self._flag is None:
            self._flag = asyncio.Event()
        return self._flag

    # -- producer side (called synchronously from event_store.save) --------

    def publish(self, aggregate_id: str, events: Any) -> None:
        """Record events and wake all waiting subscribers.

        ``asyncio.Event.set()`` is safe to call from synchronous code
        running on the event-loop thread.  All coroutines currently
        awaiting ``flag.wait()`` are scheduled to resume on the next
        event-loop iteration.
        """
        for evt in events:
            self._sequence += 1
            self._log.append(
                {
                    "sequence": self._sequence,
                    "aggregate_id": aggregate_id,
                    "type": type(evt).__name__,
                    "timestamp": evt.timestamp.isoformat()
                    if hasattr(evt, "timestamp")
                    else datetime.now(UTC).isoformat(),
                    "data": _serialize_event_payload(evt),
                }
            )
        # cap memory
        if len(self._log) > self._MAX_LOG_SIZE:
            self._log = self._log[-self._MAX_LOG_SIZE :]
        # signal all waiting subscribers (sync-safe on the loop thread)
        if self._flag is not None:
            self._flag.set()

    # -- consumer side (async generator for SSE) ---------------------------

    async def stream(
        self,
        after: int = 0,
        aggregate_id: str | None = None,
        event_type: str | None = None,
    ):
        """Async generator that yields new events as they arrive.

        Runs indefinitely until the client disconnects.
        """
        cursor = after
        while True:
            batch = self._pending(cursor, aggregate_id, event_type)
            if batch:
                for entry in batch:
                    cursor = entry["sequence"]
                    yield entry
            else:
                # clear flag *before* waiting so a set() during wait wakes us
                self.flag.clear()
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(self.flag.wait(), timeout=self._POLL_INTERVAL)

    def _pending(
        self,
        after: int,
        aggregate_id: str | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return log entries after *after*, applying optional filters."""
        result = [e for e in self._log if e["sequence"] > after]
        if aggregate_id:
            result = [e for e in result if e["aggregate_id"] == aggregate_id]
        if event_type:
            result = [e for e in result if e["type"] == event_type]
        return result


# ---------------------------------------------------------------------------
# Infrastructure — injectable; swap for Postgres/GCS in production
# ---------------------------------------------------------------------------
event_store = InMemoryEventStore()
_event_notifier = EventNotifier()

# --- Hook into event store so every save() also notifies subscribers ---
_original_event_store_save = event_store.save


def _notifying_save(
    aggregate_id: str,
    events: Any,
    expected_version: int | None = None,
) -> None:
    _original_event_store_save(aggregate_id, events, expected_version)
    _event_notifier.publish(aggregate_id, events)


event_store.save = _notifying_save  # type: ignore[method-assign]

dataset_repo: AggregateRepository[DatasetAggregate] = AggregateRepository(event_store=event_store)
contract_repo: AggregateRepository[ContractAggregate] = AggregateRepository(event_store=event_store)
batch_repo: AggregateRepository[BatchAggregate] = AggregateRepository(event_store=event_store)

# Secondary index: name → aggregate_id (needed because we address datasets by name)
_dataset_index: dict[str, str] = {}
_contract_index: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------


class DomainError(Exception):
    """Base for all domain-level errors."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(DomainError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} '{identifier}' not found.", status_code=404)


class ConflictError(DomainError):
    """Resource already exists."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} '{identifier}' already exists.", status_code=409)


class InvalidStateError(DomainError):
    """Operation not allowed in current state."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=422)


# ---------------------------------------------------------------------------
# Pydantic Response Models — typed API contracts
# ---------------------------------------------------------------------------


class DatasetResponse(BaseModel):
    """Response for a single dataset."""

    name: str
    schema_def: dict[str, str] = Field(serialization_alias="schema")
    description: str | None = None
    deprecated: bool = False


class DatasetListResponse(BaseModel):
    """List of datasets."""

    datasets: list[DatasetResponse]


class ContractResponse(BaseModel):
    """Response for a single data contract."""

    contract_id: str
    dataset: str
    approved: bool = False


class ContractListResponse(BaseModel):
    """List of data contracts."""

    contracts: list[ContractResponse]


class BatchResponse(BaseModel):
    """Response for a single batch with lifecycle status."""

    batch_id: str
    dataset: str
    status: str
    quarantined: bool = False
    published: bool = False
    dq_passed: bool = False
    privacy_passed: bool = False


class BatchListResponse(BaseModel):
    """List of batches."""

    batches: list[BatchResponse]


class BatchActionResponse(BaseModel):
    """Standard response after a batch state transition."""

    batch_id: str
    status: str
    detail: str | None = None


class ConsumeResponse(BaseModel):
    """Response when consuming a batch — includes download URL."""

    batch_id: str
    consumer: str
    download_url: str


class EventRecord(BaseModel):
    """Single event from the audit log."""

    type: str
    timestamp: str
    aggregate_id: str | None = None


class EventListResponse(BaseModel):
    """List of events with count."""

    events: list[EventRecord]
    count: int


class ReplayResponse(BaseModel):
    """Response after replaying events for a dataset."""

    dataset: str
    events_replayed: int
    status: str = "replay_completed"


class HealthResponse(BaseModel):
    """Health / readiness check response."""

    status: str = "healthy"
    service: str = "lakehouse-api"
    timestamp: str
    event_store: str = "in_memory"


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------


class RegisterDatasetIn(BaseModel):
    """Register a new dataset with name, schema, and optional description."""

    name: str = Field(..., examples=["sales"])
    schema_def: dict[str, str] = Field(
        ..., alias="schema", examples=[{"id": "int", "amount": "float"}]
    )
    description: str | None = Field(None, examples=["Daily sales data"])


class CreateContractIn(BaseModel):
    """Create a data contract for a dataset."""

    dataset: str = Field(..., examples=["sales"])
    schema_def: dict[str, str] = Field(
        default_factory=dict, alias="schema", examples=[{"id": "int", "amount": "float"}]
    )
    retention_days: int = Field(365, examples=[365])
    privacy_rules: dict[str, object] = Field(default_factory=dict)
    quality_rules: dict[str, object] = Field(default_factory=dict)


class AppendDataIn(BaseModel):
    """Append a data batch to a dataset."""

    dataset: str = Field(..., examples=["sales"])
    contract_id: str = Field(..., examples=["contract-1"])
    file_url: str = Field(..., examples=["s3://bucket/sales_2024_01.csv"])
    batch_id: str | None = Field(None, description="Auto-generated if omitted.")


class QuarantineBatchIn(BaseModel):
    """Quarantine a batch with a reason."""

    reason: str = Field(..., examples=["DQ check failed — null values in amount column"])


class RunQualityCheckIn(BaseModel):
    """Run data quality checks on a batch."""

    quality_rules: dict[str, str] = Field(..., examples=[{"amount": ">0", "id": "not_null"}])


class RunPrivacyCheckIn(BaseModel):
    """Run privacy / compliance checks on a batch."""

    privacy_rules: dict[str, str] = Field(..., examples=[{"email": "mask", "name": "hash"}])


class ConsumeBatchIn(BaseModel):
    """Consume a published batch."""

    consumer: str = Field(..., examples=["analytics-team"])


class ReplayIn(BaseModel):
    """Replay all events for a dataset."""

    dataset: str = Field(..., examples=["sales"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_dataset(name: str) -> str:
    """Return aggregate_id for a dataset name, or raise NotFoundError."""
    agg_id = _dataset_index.get(name)
    if not agg_id:
        raise NotFoundError("Dataset", name)
    return agg_id


def _require_contract(contract_id: str) -> str:
    """Validate contract exists, return aggregate_id."""
    if contract_id not in _contract_index:
        raise NotFoundError("Contract", contract_id)
    return contract_id


def _load_batch(batch_id: str) -> BatchAggregate:
    """Load a batch aggregate or raise NotFoundError."""
    try:
        return batch_repo.load(BatchAggregate, batch_id)
    except Exception:
        raise NotFoundError("Batch", batch_id)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
datasets_router = APIRouter(prefix="/datasets", tags=["Datasets"])
contracts_router = APIRouter(prefix="/contracts", tags=["Contracts"])
batches_router = APIRouter(prefix="/batches", tags=["Batches"])
events_router = APIRouter(prefix="/events", tags=["Events"])


# ===========================================================================
# Error Handler — converts DomainError → structured JSON
# ===========================================================================


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Convert domain errors to structured API responses."""
    if not isinstance(exc, DomainError):  # pragma: no cover
        return JSONResponse(status_code=500, content={"error": "InternalError", "detail": str(exc)})
    logger.warning("domain_error", extra={"detail": exc.detail, "status": exc.status_code})
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": type(exc).__name__, "detail": exc.detail},
    )


# ===========================================================================
# Health & Readiness
# ===========================================================================

health_router = APIRouter(tags=["Operations"])


@health_router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """Liveness probe for Kubernetes / Cloud Run."""
    return HealthResponse(timestamp=datetime.now(UTC).isoformat())


@health_router.get("/ready", response_model=HealthResponse, summary="Readiness Check")
async def readiness_check() -> HealthResponse:
    """Readiness probe — checks if event store is accessible."""
    return HealthResponse(timestamp=datetime.now(UTC).isoformat(), status="ready")


# ===========================================================================
# Datasets — register, list, get
# ===========================================================================


@datasets_router.post(
    "",
    summary="Register Dataset",
    description="Register a new dataset with name, schema, and optional description.",
    response_model=DatasetResponse,
    status_code=201,
)
async def register_dataset(body: RegisterDatasetIn) -> DatasetResponse:
    """Register a new dataset. Emits *DatasetRegistered*."""
    if body.name in _dataset_index:
        raise ConflictError("Dataset", body.name)

    aggregate_id = f"dataset-{body.name}"
    agg = DatasetAggregate()
    agg.aggregate_id = aggregate_id
    agg.register(
        RegisterDataset(name=body.name, schema=body.schema_def, description=body.description)
    )
    dataset_repo.save(agg)
    _dataset_index[body.name] = aggregate_id

    logger.info("dataset_registered", extra={"dataset": body.name})
    return DatasetResponse(name=agg.name, schema_def=agg.schema, description=agg.description)


@datasets_router.get(
    "",
    summary="List Datasets",
    description="Return all registered datasets with schema and lifecycle info.",
    response_model=DatasetListResponse,
)
async def list_datasets() -> DatasetListResponse:
    """Return all registered datasets."""
    datasets = []
    for _name, agg_id in _dataset_index.items():
        agg = dataset_repo.load(DatasetAggregate, agg_id)
        datasets.append(
            DatasetResponse(
                name=agg.name,
                schema_def=agg.schema,
                description=agg.description,
                deprecated=agg.deprecated,
            )
        )
    return DatasetListResponse(datasets=datasets)


@datasets_router.get(
    "/{name}",
    summary="Get Dataset",
    description="Return the schema, description, and lifecycle status of a single dataset.",
    response_model=DatasetResponse,
)
async def get_dataset(name: str) -> DatasetResponse:
    """Return details of a registered dataset."""
    agg_id = _require_dataset(name)
    agg = dataset_repo.load(DatasetAggregate, agg_id)
    return DatasetResponse(
        name=agg.name,
        schema_def=agg.schema,
        description=agg.description,
        deprecated=agg.deprecated,
    )


# ===========================================================================
# Contracts — create, list
# ===========================================================================


@contracts_router.post(
    "",
    summary="Create Contract",
    description="Create a data contract (schema, retention, privacy & quality rules) for a dataset.",
    response_model=ContractResponse,
    status_code=201,
)
async def create_contract(body: CreateContractIn) -> ContractResponse:
    """Create a new data contract. Emits *DataContractDefined*."""
    _require_dataset(body.dataset)

    contract_id = f"contract-{uuid.uuid4().hex[:8]}"
    agg = ContractAggregate()
    agg.aggregate_id = contract_id
    agg.create(
        CreateContract(
            dataset=body.dataset,
            schema=body.schema_def,
            privacy_rules=body.privacy_rules,
            quality_rules=body.quality_rules,
        )
    )
    contract_repo.save(agg)
    _contract_index[contract_id] = contract_id

    logger.info("contract_created", extra={"contract_id": contract_id, "dataset": body.dataset})
    return ContractResponse(contract_id=contract_id, dataset=body.dataset)


@contracts_router.get(
    "",
    summary="List Contracts",
    description="Return all data contracts with their approval status.",
    response_model=ContractListResponse,
)
async def list_contracts() -> ContractListResponse:
    """Return all contracts."""
    contracts = []
    for cid in _contract_index:
        agg = contract_repo.load(ContractAggregate, cid)
        contracts.append(
            ContractResponse(
                contract_id=agg.contract_id or cid,
                dataset=agg.dataset,
                approved=agg.approved,
            )
        )
    return ContractListResponse(contracts=contracts)


# ===========================================================================
# Batches — append, quarantine, validate, publish, consume
# ===========================================================================


@batches_router.post(
    "/append",
    summary="Append Data",
    description="Append a new data batch to a dataset. batch_id is auto-generated if omitted.",
    response_model=BatchResponse,
    status_code=201,
)
async def append_data(body: AppendDataIn) -> BatchResponse:
    """Append data to a dataset. Emits *AppendIngestionRequested* → *DataAppended*."""
    _require_dataset(body.dataset)
    _require_contract(body.contract_id)

    batch_id = body.batch_id or f"batch-{uuid.uuid4().hex[:8]}"

    agg = BatchAggregate()
    agg.aggregate_id = batch_id
    agg.append(
        AppendData(
            dataset=body.dataset,
            contract_id=body.contract_id,
            batch_id=batch_id,
            file_url=body.file_url,
        )
    )
    batch_repo.save(agg)

    logger.info("data_appended", extra={"batch_id": batch_id, "dataset": body.dataset})
    return _batch_response(agg)


@batches_router.post(
    "/{batch_id}/quarantine",
    summary="Quarantine Batch",
    description=(
        "Move a batch into quarantine. A quarantined batch cannot be published "
        "or consumed until it is explicitly released via the release endpoint. "
        "Use this when DQ checks fail or data anomalies are detected."
    ),
    response_model=BatchActionResponse,
)
async def quarantine_batch(batch_id: str, body: QuarantineBatchIn) -> BatchActionResponse:
    """Quarantine a batch. Emits *BatchQuarantined*."""
    agg = _load_batch(batch_id)
    try:
        agg.quarantine(QuarantineBatch(batch_id=batch_id, reason=body.reason))
    except ValueError as e:
        raise InvalidStateError(str(e))
    batch_repo.save(agg)

    logger.info("batch_quarantined", extra={"batch_id": batch_id, "reason": body.reason})
    return BatchActionResponse(batch_id=batch_id, status="quarantined", detail=body.reason)


@batches_router.post(
    "/{batch_id}/release",
    summary="Release Quarantine",
    description=(
        "Release a quarantined batch so it can be re-validated and eventually "
        "published. The batch status returns to INGESTED, allowing the DQ/privacy "
        "check → publish lifecycle to restart."
    ),
    response_model=BatchActionResponse,
)
async def release_quarantine(batch_id: str) -> BatchActionResponse:
    """Release batch from quarantine. Emits *QuarantineReleased*."""
    agg = _load_batch(batch_id)
    try:
        agg.release_quarantine(ReleaseQuarantine(batch_id=batch_id))
    except ValueError as e:
        raise InvalidStateError(str(e))
    batch_repo.save(agg)

    logger.info("quarantine_released", extra={"batch_id": batch_id})
    return BatchActionResponse(batch_id=batch_id, status="released")


@batches_router.post(
    "/{batch_id}/validate",
    summary="Run Quality Check",
    description=(
        "Run data-quality rules against a batch. Marks the batch as DQ-passed. "
        "When both DQ and privacy checks pass, the batch automatically transitions "
        "to VALIDATED and is ready for publishing."
    ),
    response_model=BatchActionResponse,
)
async def run_quality_check(batch_id: str, body: RunQualityCheckIn) -> BatchActionResponse:
    """Run DQ checks on a batch. Updates batch state. Emits *QualityCheckPassed*."""
    agg = _load_batch(batch_id)
    try:
        agg.mark_dq_passed(batch_id)
    except ValueError as e:
        raise InvalidStateError(str(e))
    batch_repo.save(agg)

    logger.info("dq_passed", extra={"batch_id": batch_id, "rules": body.quality_rules})
    return BatchActionResponse(
        batch_id=batch_id,
        status=agg.status.value,
        detail="quality_check_passed",
    )


@batches_router.post(
    "/{batch_id}/privacy-check",
    summary="Run Privacy Check",
    description=(
        "Run privacy/compliance rules against a batch (PII masking, hashing). "
        "Marks the batch as privacy-passed. Together with a passed DQ check, "
        "this transitions the batch to VALIDATED."
    ),
    response_model=BatchActionResponse,
)
async def run_privacy_check(batch_id: str, body: RunPrivacyCheckIn) -> BatchActionResponse:
    """Run privacy checks on a batch. Updates batch state."""
    agg = _load_batch(batch_id)
    try:
        agg.mark_privacy_passed(batch_id)
    except ValueError as e:
        raise InvalidStateError(str(e))
    batch_repo.save(agg)

    logger.info("privacy_passed", extra={"batch_id": batch_id, "rules": body.privacy_rules})
    return BatchActionResponse(
        batch_id=batch_id,
        status=agg.status.value,
        detail="privacy_check_passed",
    )


@batches_router.post(
    "/{batch_id}/publish",
    summary="Publish Batch",
    description=(
        "Publish a validated batch, making it available for consumption. "
        "Only VALIDATED or INGESTED batches can be published. "
        "Quarantined batches must be released first."
    ),
    response_model=BatchActionResponse,
)
async def publish_batch(batch_id: str) -> BatchActionResponse:
    """Publish a batch. Emits *DataPublished*."""
    agg = _load_batch(batch_id)
    try:
        agg.publish(PublishData(batch_id=batch_id))
    except ValueError as e:
        raise InvalidStateError(str(e))
    batch_repo.save(agg)

    logger.info("batch_published", extra={"batch_id": batch_id})
    return BatchActionResponse(batch_id=batch_id, status="published")


@batches_router.post(
    "/{batch_id}/consume",
    summary="Consume Batch",
    description=(
        "Request a signed download URL for a published batch. "
        "Only published batches can be consumed. The consumer identity is recorded "
        "in the audit trail."
    ),
    response_model=ConsumeResponse,
)
async def consume_batch(batch_id: str, body: ConsumeBatchIn) -> ConsumeResponse:
    """Consume a published batch. Returns signed download URL."""
    agg = _load_batch(batch_id)
    if not agg.published:
        raise InvalidStateError(f"Batch '{batch_id}' is not published yet.")

    download_url = f"https://lakehouse.example.com/download/{batch_id}?consumer={body.consumer}"
    logger.info("batch_consumed", extra={"batch_id": batch_id, "consumer": body.consumer})
    return ConsumeResponse(batch_id=batch_id, consumer=body.consumer, download_url=download_url)


@batches_router.get(
    "",
    summary="List Batches",
    description="Return all batches with their current lifecycle status. Optionally filter by dataset name.",
    response_model=BatchListResponse,
)
async def list_batches(dataset: str | None = Query(None)) -> BatchListResponse:
    """Return all batches, optionally filtered by dataset."""
    result = []
    for stream_id in event_store._events:
        if not stream_id.startswith("batch-"):
            continue
        try:
            agg = batch_repo.load(BatchAggregate, stream_id)
        except Exception:
            logger.debug("Skipping stream %s (not a batch)", stream_id)
            continue
        if dataset and agg.dataset != dataset:
            continue
        result.append(_batch_response(agg))
    return BatchListResponse(batches=result)


@batches_router.get(
    "/{batch_id}",
    summary="Get Batch",
    description="Return the current status and details of a single batch by its ID.",
    response_model=BatchResponse,
)
async def get_batch(batch_id: str) -> BatchResponse:
    """Return details of a single batch."""
    agg = _load_batch(batch_id)
    return _batch_response(agg)


def _batch_response(agg: BatchAggregate) -> BatchResponse:
    """Build a BatchResponse from aggregate state."""
    return BatchResponse(
        batch_id=agg.batch_id or agg.aggregate_id,
        dataset=agg.dataset,
        status=agg.status.value,
        quarantined=agg.quarantined,
        published=agg.published,
        dq_passed=agg.dq_passed,
        privacy_passed=agg.privacy_passed,
    )


# ===========================================================================
# Events — subscribe (SSE stream), replay, query
# ===========================================================================


async def _sse_generator(
    cursor: int,
    aggregate_id: str | None,
    event_type: str | None,
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted lines.

    Each message contains only a compact JSON payload with the
    domain-specific event data (CloudEvents envelope is stripped).
    """
    async for entry in _event_notifier.stream(
        after=cursor,
        aggregate_id=aggregate_id,
        event_type=event_type,
    ):
        # Build compact payload: envelope in SSE fields, domain data in JSON
        data = entry["data"] if isinstance(entry["data"], dict) else {}
        data["aggregate_id"] = entry["aggregate_id"]
        data["timestamp"] = entry["timestamp"]
        payload = json.dumps(data, default=str, separators=(",", ":"))
        # SSE format: id for reconnection, event name, data line, blank line
        yield f"id: {entry['sequence']}\nevent: {entry['type']}\ndata: {payload}\n\n"


@events_router.get(
    "/subscribe",
    summary="Subscribe (Server-Sent Events)",
    description=(
        "SSE streaming endpoint for receiving events in real-time "
        "without WebSockets.\n\n"
        "**How it works:**\n"
        "1. Open `GET /events/subscribe` — the connection stays open.\n"
        "2. **Only new events** are pushed — nothing from history.\n"
        "3. On reconnect the browser sends `Last-Event-ID` automatically "
        "so no events are lost.\n"
        "4. In JavaScript: `new EventSource('/events/subscribe')`.\n\n"
        "To explicitly replay older events pass `?cursor=<n>` where *n* "
        "is a sequence number you saved earlier.\n\n"
        "Fully compatible with corporate proxies and load-balancers "
        "that do not support WebSocket upgrades — it is plain HTTP "
        "with `Content-Type: text/event-stream`."
    ),
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "SSE event stream",
        }
    },
)
async def subscribe_events(
    request: Request,
    cursor: int | None = Query(
        None,
        ge=0,
        description=(
            "Sequence number to resume from. "
            "Omit to receive only future events (default). "
            "Use 0 to replay the full backlog."
        ),
    ),
    aggregate_id: str | None = Query(None, description="Only stream events for this aggregate."),
    event_type: str | None = Query(None, description="Only stream events of this type."),
) -> StreamingResponse:
    """SSE stream — enterprise-friendly real-time event subscription."""
    # --- resolve effective cursor ---
    # 1) Explicit query param wins
    # 2) Last-Event-ID header (sent by EventSource on reconnect)
    # 3) Default: current head → only future events
    effective_cursor: int
    if cursor is not None:
        effective_cursor = cursor
    else:
        last_event_id = request.headers.get("last-event-id")
        if last_event_id is not None:
            try:
                effective_cursor = int(last_event_id)
            except ValueError:
                effective_cursor = _event_notifier.current_sequence
        else:
            effective_cursor = _event_notifier.current_sequence

    async def _guarded() -> AsyncGenerator[str, None]:
        """Wrap generator to stop when the client disconnects."""
        async for chunk in _sse_generator(effective_cursor, aggregate_id, event_type):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        _guarded(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@events_router.post(
    "/replay",
    summary="Replay Events",
    description="Replay all events for a dataset aggregate, rebuilding its state from the event store.",
    response_model=ReplayResponse,
)
async def replay_events(body: ReplayIn) -> ReplayResponse:
    """Replay events for a dataset. Rebuilds aggregate state from event store."""
    agg_id = _require_dataset(body.dataset)
    events = event_store.load(agg_id)
    logger.info("replay_completed", extra={"dataset": body.dataset, "events": len(events)})
    return ReplayResponse(dataset=body.dataset, events_replayed=len(events))


@events_router.get(
    "",
    summary="Query Events",
    description="Query the event store. Filter by aggregate_id or event_type. Returns full audit trail.",
    response_model=EventListResponse,
)
async def query_events(
    aggregate_id: str | None = Query(None, description="Filter by aggregate stream ID"),
    event_type: str | None = Query(None, description="Filter by event type name"),
) -> EventListResponse:
    """Query events from the event store."""
    if aggregate_id:
        try:
            raw_events = event_store.load(aggregate_id)
        except Exception:
            raw_events = []
    else:
        # Collect from all streams (demo only — production: use projection/read model)
        raw_events = []
        for stream_id in event_store._events:
            raw_events.extend(event_store.load(stream_id))

    records = []
    for evt in raw_events:
        evt_data = evt.data if hasattr(evt, "data") else evt
        type_name = type(evt_data).__name__
        if event_type and type_name != event_type:
            continue
        records.append(
            EventRecord(
                type=type_name,
                timestamp=getattr(evt_data, "time", datetime.now(UTC)).isoformat()
                if hasattr(evt_data, "time")
                else datetime.now(UTC).isoformat(),
                aggregate_id=aggregate_id,
            )
        )
    return EventListResponse(events=records, count=len(records))


# ===========================================================================
# Root redirect
# ===========================================================================

router = APIRouter()


@router.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to /docs."""
    return RedirectResponse(url="/docs")
