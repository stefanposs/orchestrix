from dataclasses import dataclass, field
from datetime import datetime

# --- ENUMS ---
from enum import Enum
from typing import Any

from orchestrix.core.messaging.message import Command, Event


class JobStatus(Enum):
    """Enumeration of anonymization job statuses."""

    PENDING = "PENDING"
    DRY_RUN_STARTED = "DRY_RUN_STARTED"
    DRY_RUN_COMPLETED = "DRY_RUN_COMPLETED"
    DRY_RUN_FAILED = "DRY_RUN_FAILED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    ANONYMIZATION_STARTED = "ANONYMIZATION_STARTED"
    ANONYMIZATION_COMPLETED = "ANONYMIZATION_COMPLETED"
    ANONYMIZATION_FAILED = "ANONYMIZATION_FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class AnonymizationStrategy(Enum):
    """Enumeration of anonymization strategies."""

    MASK = "MASK"
    HASH = "HASH"
    REDACT = "REDACT"
    NULLIFY = "NULLIFY"
    CUSTOM = "CUSTOM"


class ColumnType(Enum):
    """Enumeration of column types for anonymization rules."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


# --- TABLE SCHEMA ---
@dataclass(frozen=True, kw_only=True)
class TableSchema:
    """Schema information for a database table."""

    database: str
    schema_name: str
    table_name: str
    columns: list[str]


# --- ANONYMIZATION RULE ---
@dataclass(frozen=True, kw_only=True)
class AnonymizationRule:
    """Rule for anonymizing a specific column."""

    column_name: str
    strategy: AnonymizationStrategy
    preserve_format: bool = False
    preserve_null: bool = False
    column_type: ColumnType = ColumnType.STRING


# --- DRY RUN RESULT ---
@dataclass(frozen=True, kw_only=True)
class DryRunResult:
    """Result of a dry run anonymization."""

    job_id: str
    affected_rows: int
    affected_columns: list[str]
    estimated_duration_seconds: float
    warnings: list[str]
    sample_before: dict[str, list[Any]]
    sample_after: dict[str, list[Any]]


# --- EVENTS ---
@dataclass(frozen=True, kw_only=True)
class AnonymizationJobCreated(Event):
    """Event emitted when an anonymization job is created."""

    job_id: str
    table_schema: TableSchema
    rules: list[AnonymizationRule]
    requester: str
    reason: str
    created_at: datetime


@dataclass(frozen=True, kw_only=True)
class AnonymizationStarted(Event):
    """Event emitted when anonymization is started for a job."""

    job_id: str
    backup_location: str
    started_at: datetime


@dataclass(frozen=True, kw_only=True)
class ColumnAnonymized(Event):
    """Event emitted when a column is anonymized in a job."""

    job_id: str
    column_name: str
    strategy: str
    rows_affected: int
    anonymized_at: datetime


@dataclass(frozen=True, kw_only=True)
class AnonymizationCompleted(Event):
    """Event emitted when anonymization is completed for a job."""

    job_id: str
    total_rows_affected: int
    total_columns_affected: int
    duration_seconds: float
    completed_at: datetime


@dataclass(frozen=True, kw_only=True)
class AnonymizationFailed(Event):
    """Event emitted when anonymization fails for a job."""

    job_id: str
    reason: str
    column_name: str | None = None
    failed_at: datetime = field(
        default_factory=lambda: datetime.now(__import__("datetime").timezone.utc)
    )


@dataclass(frozen=True, kw_only=True)
class AnonymizationRolledBack(Event):
    """Event emitted when an anonymization job is rolled back."""

    job_id: str
    backup_restored_from: str
    rolled_back_at: datetime


@dataclass(frozen=True, kw_only=True)
class DryRunStarted(Event):
    """Event emitted when a dry run is started for a job."""

    job_id: str
    table_schema: TableSchema
    started_at: datetime


@dataclass(frozen=True, kw_only=True)
class DryRunCompleted(Event):
    """Event emitted when a dry run is completed for a job."""

    job_id: str
    result: DryRunResult
    completed_at: datetime


@dataclass(frozen=True, kw_only=True)
class DryRunFailed(Event):
    """Event emitted when a dry run fails for a job."""

    job_id: str
    reason: str
    failed_at: datetime


@dataclass(frozen=True, kw_only=True)
class ValidationPassed(Event):
    """Event emitted when validation has passed for a job."""

    job_id: str
    approved_by: str
    approved_at: datetime


# --- Saga/Workflow Commands ---
@dataclass(frozen=True, kw_only=True)
class ApproveJob(Command):
    """Command to approve a job."""

    job_id: str
    approver: str


@dataclass(frozen=True, kw_only=True)
class RollbackAnonymization(Command):
    """Command to roll back anonymization for a job."""

    job_id: str
    reason: str


@dataclass(frozen=True, kw_only=True)
class StartAnonymization(Command):
    """Command to start anonymization for a job."""

    job_id: str
    columns: list[str]


@dataclass(frozen=True, kw_only=True)
class StartDryRun(Command):
    """Command to start a dry run for a job."""

    job_id: str
    params: dict[str, Any]


"""Domain models, commands, and events for the self-service Lakehouse demo."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestrix.core.messaging.message import Command, Event


# --- Dataset Lifecycle ---
@dataclass(frozen=True, kw_only=True)
class RegisterDataset(Command):
    """Command to register a new dataset."""

    name: str
    schema: dict[str, str]
    description: str | None = None


@dataclass(frozen=True, kw_only=True)
class DatasetRegistered(Event):
    """Event emitted when a dataset is registered."""

    name: str
    schema: dict[str, str]
    description: str | None
    registered_at: datetime


@dataclass(frozen=True, kw_only=True)
class ActivateDatasetVersion(Command):
    """Command to activate a dataset version."""

    name: str
    version: str


@dataclass(frozen=True, kw_only=True)
class DatasetVersionActivated(Event):
    """Event emitted when a dataset version is activated."""

    name: str
    version: str
    activated_at: datetime


@dataclass(frozen=True, kw_only=True)
class DeprecateDataset(Command):
    """Command to deprecate a dataset."""

    name: str


@dataclass(frozen=True, kw_only=True)
class DatasetDeprecated(Event):
    """Event emitted when a dataset is deprecated."""

    name: str
    deprecated_at: datetime


# --- Data Contracts ---
@dataclass(frozen=True, kw_only=True)
class CreateContract(Command):
    """Command to create a new contract."""

    dataset: str
    schema: dict[str, str]
    privacy_rules: dict[str, Any]
    quality_rules: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class DataContractDefined(Event):
    """Event emitted when a contract is defined."""

    dataset: str
    contract_id: str
    schema: dict[str, str]
    privacy_rules: dict[str, Any]
    quality_rules: dict[str, Any]
    defined_at: datetime


@dataclass(frozen=True, kw_only=True)
class ApproveContract(Command):
    """Command to approve a contract."""

    contract_id: str
    approver: str


@dataclass(frozen=True, kw_only=True)
class DataContractApproved(Event):
    """Event emitted when a contract is approved."""

    contract_id: str
    approved_by: str
    approved_at: datetime


@dataclass(frozen=True, kw_only=True)
class DeclineContract(Command):
    """Command to decline a contract."""

    contract_id: str
    reason: str


@dataclass(frozen=True, kw_only=True)
class DataContractDeprecated(Event):
    """Event emitted when a contract is deprecated."""

    contract_id: str
    deprecated_at: datetime


@dataclass(frozen=True, kw_only=True)
class UpdateContract(Command):
    """Command to update a contract."""

    contract_id: str
    schema: dict[str, str]
    privacy_rules: dict[str, Any]
    quality_rules: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class DataContractUpdated(Event):
    """Event emitted when a contract is updated."""

    contract_id: str
    updated_at: datetime


# --- Append-Only Ingestion ---
@dataclass(frozen=True, kw_only=True)
class AppendData(Command):
    """Command to append a data batch."""

    dataset: str
    contract_id: str
    batch_id: str
    file_url: str


@dataclass(frozen=True, kw_only=True)
class AppendIngestionRequested(Event):
    """Event emitted when ingestion is requested."""

    dataset: str
    contract_id: str
    batch_id: str
    file_url: str
    requested_at: datetime


@dataclass(frozen=True, kw_only=True)
class DataAppended(Event):
    """Event emitted when data is appended."""

    dataset: str
    contract_id: str
    batch_id: str
    appended_at: datetime


@dataclass(frozen=True, kw_only=True)
class RequestReplay(Command):
    """Command to request a replay."""

    dataset: str
    batch_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class ReplayRequested(Event):
    """Event emitted when a replay is requested."""

    dataset: str
    batch_id: str | None
    requested_at: datetime


@dataclass(frozen=True, kw_only=True)
class ReplayCompleted(Event):
    """Event emitted when a replay is completed."""

    dataset: str
    batch_id: str | None
    completed_at: datetime


# --- Schema Validation & Evolution ---
@dataclass(frozen=True, kw_only=True)
class ValidateSchema(Command):
    """Command to validate a schema."""

    batch_id: str
    contract_id: str


@dataclass(frozen=True, kw_only=True)
class SchemaValidated(Event):
    """Event emitted when a schema is validated."""

    batch_id: str
    contract_id: str
    validated_at: datetime


@dataclass(frozen=True, kw_only=True)
class SchemaValidationFailed(Event):
    """Event emitted when schema validation fails."""

    batch_id: str
    contract_id: str
    reason: str
    failed_at: datetime


@dataclass(frozen=True, kw_only=True)
class UpdateSchemaVersion(Command):
    """Command to update schema version."""

    contract_id: str
    new_schema: dict[str, str]


@dataclass(frozen=True, kw_only=True)
class SchemaVersionUpdated(Event):
    """Event emitted when schema version is updated."""

    contract_id: str
    new_schema: dict[str, str]
    updated_at: datetime


# --- Data Anonymization / Privacy ---
@dataclass(frozen=True, kw_only=True)
class AnonymizeData(Command):
    """Command to anonymize data."""

    batch_id: str
    privacy_rules: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class DataAnonymized(Event):
    """Event emitted when data is anonymized."""

    batch_id: str
    anonymized_at: datetime


# --- Data Quality Checks ---
@dataclass(frozen=True, kw_only=True)
class RunQualityCheck(Command):
    """Command to run a data quality check."""

    batch_id: str
    quality_rules: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class QualityCheckPassed(Event):
    """Event emitted when a quality check passes."""

    batch_id: str
    checked_at: datetime


@dataclass(frozen=True, kw_only=True)
class QualityCheckFailed(Event):
    """Event emitted when a quality check fails."""

    batch_id: str
    reason: str
    failed_at: datetime


# --- Quarantine / Isolation ---
@dataclass(frozen=True, kw_only=True)
class QuarantineBatch(Command):
    """Command to quarantine a batch."""

    batch_id: str
    reason: str


@dataclass(frozen=True, kw_only=True)
class BatchQuarantined(Event):
    """Event emitted when a batch is quarantined."""

    batch_id: str
    reason: str
    quarantined_at: datetime


@dataclass(frozen=True, kw_only=True)
class ReleaseQuarantine(Command):
    """Command to release a batch from quarantine."""

    batch_id: str


@dataclass(frozen=True, kw_only=True)
class QuarantineReleased(Event):
    """Event emitted when a batch is released from quarantine."""

    batch_id: str
    released_at: datetime


# --- Publication & Consumption ---
@dataclass(frozen=True, kw_only=True)
class PublishData(Command):
    """Command to publish a batch for consumption."""

    batch_id: str


@dataclass(frozen=True, kw_only=True)
class DataPublished(Event):
    """Event emitted when a batch is published."""

    batch_id: str
    published_at: datetime


@dataclass(frozen=True, kw_only=True)
class GrantConsumption(Command):
    """Command to grant consumption rights for a batch."""

    batch_id: str
    consumer: str


@dataclass(frozen=True, kw_only=True)
class ConsumptionGranted(Event):
    """Event emitted when consumption rights are granted."""

    batch_id: str
    consumer: str
    granted_at: datetime


# --- Signed URL / Self-Service ---
@dataclass(frozen=True, kw_only=True)
class GenerateSignedUrl(Command):
    """Command to generate a signed URL for upload/download."""

    dataset: str
    filename: str
    expires_in: int


@dataclass(frozen=True, kw_only=True)
class SignedUrlCreated(Event):
    """Event emitted when a signed URL is created."""

    dataset: str
    filename: str
    url: str
    expires_at: datetime
