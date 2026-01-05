"""Domain models for lakehouse data anonymization."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from orchestrix.core.messaging.message import Command, Event


class AnonymizationStrategy(str, Enum):
    """Anonymization techniques."""

    MASKING = "masking"  # Replace with '*****'
    HASHING = "hashing"  # SHA-256 hash
    TOKENIZATION = "tokenization"  # Replace with random token
    GENERALIZATION = "generalization"  # Reduce precision (e.g., age ranges)
    SUPPRESSION = "suppression"  # Delete entirely
    PSEUDONYMIZATION = "pseudonymization"  # Consistent fake data
    AGGREGATION = "aggregation"  # Group into buckets
    NOISE = "noise"  # Add random noise to numbers


class JobStatus(str, Enum):
    """Anonymization job states."""

    PENDING = "pending"
    DRY_RUN_STARTED = "dry_run_started"
    DRY_RUN_COMPLETED = "dry_run_completed"
    DRY_RUN_FAILED = "dry_run_failed"
    VALIDATION_PASSED = "validation_passed"
    ANONYMIZATION_STARTED = "anonymization_started"
    ANONYMIZATION_COMPLETED = "anonymization_completed"
    ANONYMIZATION_FAILED = "anonymization_failed"
    ROLLED_BACK = "rolled_back"


class ColumnType(str, Enum):
    """Data column types."""

    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    SALARY = "salary"
    GENERIC_PII = "generic_pii"


@dataclass(frozen=True)
class AnonymizationRule:
    """Rule defining how to anonymize a column."""

    column_name: str
    column_type: ColumnType
    strategy: AnonymizationStrategy
    preserve_format: bool = False  # Keep format (e.g., email structure)
    preserve_null: bool = True  # Keep NULL values as NULL


@dataclass(frozen=True)
class TableSchema:
    """Schema of a table to be anonymized."""

    database: str
    schema_name: str
    table_name: str
    columns: list[str]
    row_count: int
    primary_keys: list[str]


@dataclass(frozen=True)
class DryRunResult:
    """Result of dry-run validation."""

    affected_rows: int
    affected_columns: list[str]
    estimated_duration_seconds: float
    warnings: list[str]
    sample_before: dict[str, list[Any]]  # Sample data before
    sample_after: dict[str, list[Any]]  # Sample data after (preview)


# Events


@dataclass(frozen=True, kw_only=True)
class AnonymizationJobCreated(Event):
    """Anonymization job was created."""

    job_id: str
    table_schema: TableSchema
    rules: list[AnonymizationRule]
    requester: str
    reason: str
    created_at: datetime


@dataclass(frozen=True, kw_only=True)
class DryRunStarted(Event):
    """Dry-run validation started."""

    job_id: str
    table_schema: TableSchema
    started_at: datetime


@dataclass(frozen=True, kw_only=True)
class DryRunCompleted(Event):
    """Dry-run validation completed successfully."""

    job_id: str
    result: DryRunResult
    completed_at: datetime


@dataclass(frozen=True, kw_only=True)
class DryRunFailed(Event):
    """Dry-run validation failed."""

    job_id: str
    reason: str
    failed_at: datetime


@dataclass(frozen=True, kw_only=True)
class ValidationPassed(Event):
    """Dry-run validation passed and job approved."""

    job_id: str
    approved_by: str
    approved_at: datetime


@dataclass(frozen=True, kw_only=True)
class AnonymizationStarted(Event):
    """Actual anonymization started."""

    job_id: str
    backup_location: str  # Backup before anonymization
    started_at: datetime


@dataclass(frozen=True, kw_only=True)
class ColumnAnonymized(Event):
    """A column was anonymized."""

    job_id: str
    column_name: str
    strategy: AnonymizationStrategy
    rows_affected: int
    anonymized_at: datetime


@dataclass(frozen=True, kw_only=True)
class AnonymizationCompleted(Event):
    """Anonymization completed successfully."""

    job_id: str
    total_rows_affected: int
    total_columns_affected: int
    duration_seconds: float
    completed_at: datetime


@dataclass(frozen=True, kw_only=True)
class AnonymizationFailed(Event):
    """Anonymization failed."""

    job_id: str
    reason: str
    column_name: str | None
    failed_at: datetime


@dataclass(frozen=True, kw_only=True)
class AnonymizationRolledBack(Event):
    """Anonymization was rolled back."""

    job_id: str
    backup_restored_from: str
    rolled_back_at: datetime


# Commands


@dataclass(frozen=True, kw_only=True)
class CreateAnonymizationJob(Command):
    """Create a new anonymization job."""

    job_id: str
    table_schema: TableSchema
    rules: list[AnonymizationRule]
    requester: str
    reason: str


@dataclass(frozen=True, kw_only=True)
class StartDryRun(Command):
    """Start dry-run validation."""

    job_id: str


@dataclass(frozen=True, kw_only=True)
class ApproveJob(Command):
    """Approve job after dry-run."""

    job_id: str
    approver: str


@dataclass(frozen=True, kw_only=True)
class StartAnonymization(Command):
    """Start actual anonymization."""

    job_id: str


@dataclass(frozen=True, kw_only=True)
class RollbackAnonymization(Command):
    """Rollback anonymization from backup."""

    job_id: str
