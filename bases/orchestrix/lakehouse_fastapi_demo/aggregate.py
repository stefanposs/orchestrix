from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from orchestrix.core.eventsourcing.aggregate import AggregateRoot

from .models import (
    ActivateDatasetVersion,
    AnonymizationCompleted,
    AnonymizationFailed,
    AnonymizationJobCreated,
    AnonymizationRolledBack,
    AnonymizationRule,
    AnonymizationStarted,
    AppendData,
    AppendIngestionRequested,
    ApproveContract,
    BatchQuarantined,
    ColumnAnonymized,
    CreateContract,
    DataAppended,
    DataContractApproved,
    DataContractDefined,
    DataContractDeprecated,
    DataContractUpdated,
    DataPublished,
    DatasetDeprecated,
    DatasetRegistered,
    DatasetVersionActivated,
    DeclineContract,
    DeprecateDataset,
    DryRunCompleted,
    DryRunFailed,
    DryRunResult,
    DryRunStarted,
    JobStatus,
    PublishData,
    QuarantineBatch,
    QuarantineReleased,
    RegisterDataset,
    ReleaseQuarantine,
    TableSchema,
    UpdateContract,
    ValidationPassed,
)

# --- Dataset Aggregate ---


@dataclass
class DatasetAggregate(AggregateRoot):
    """Aggregate for dataset lifecycle management."""

    name: str = ""
    schema: dict[str, str] = field(default_factory=dict)
    description: str | None = None
    version: str | None = None
    deprecated: bool = False
    registered_at: datetime | None = None

    def register(self, cmd: RegisterDataset) -> None:
        """Register a new dataset."""
        if self.name:
            raise ValueError("Dataset already registered")
        self._apply_event(
            DatasetRegistered(
                name=cmd.name,
                schema=cmd.schema,
                description=cmd.description,
                registered_at=datetime.now(UTC),
            )
        )

    def activate_version(self, cmd: ActivateDatasetVersion) -> None:
        """Activate a new dataset version."""
        self._apply_event(
            DatasetVersionActivated(
                name=cmd.name,
                version=cmd.version,
                activated_at=datetime.now(UTC),
            )
        )

    def deprecate(self, cmd: DeprecateDataset) -> None:
        """Deprecate a dataset."""
        self._apply_event(
            DatasetDeprecated(
                name=cmd.name,
                deprecated_at=datetime.now(UTC),
            )
        )


# --- Contract Aggregate ---


@dataclass
class ContractAggregate(AggregateRoot):
    """Aggregate for contract lifecycle management."""

    contract_id: str = ""
    dataset: str = ""
    schema: dict[str, str] = field(default_factory=dict)
    privacy_rules: dict[str, Any] = field(default_factory=dict)
    quality_rules: dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    defined_at: datetime | None = None
    approved_at: datetime | None = None
    deprecated: bool = False

    def create(self, cmd: CreateContract) -> None:
        """Create a new contract."""
        self._apply_event(
            DataContractDefined(
                dataset=cmd.dataset,
                contract_id=self.aggregate_id,
                schema=cmd.schema,
                privacy_rules=cmd.privacy_rules,
                quality_rules=cmd.quality_rules,
                defined_at=datetime.now(UTC),
            )
        )

    def approve(self, cmd: ApproveContract) -> None:
        """Approve a contract."""
        self._apply_event(
            DataContractApproved(
                contract_id=self.aggregate_id,
                approved_by=cmd.approver,
                approved_at=datetime.now(UTC),
            )
        )

    def decline(self, cmd: DeclineContract) -> None:
        """Decline a contract."""
        self._apply_event(
            DataContractDeprecated(
                contract_id=self.aggregate_id,
                deprecated_at=datetime.now(UTC),
            )
        )

    def update(self, cmd: UpdateContract) -> None:
        """Update a contract."""
        self._apply_event(
            DataContractUpdated(
                contract_id=self.aggregate_id,
                updated_at=datetime.now(UTC),
            )
        )


# --- Batch Aggregate ---


@dataclass
class BatchAggregate(AggregateRoot):
    """Aggregate for batch (data ingestion) lifecycle."""

    batch_id: str = ""
    dataset: str = ""
    contract_id: str = ""
    file_url: str | None = None
    appended: bool = False
    quarantined: bool = False
    published: bool = False
    anonymized: bool = False
    dq_passed: bool = False
    events: list = field(default_factory=list)

    def append(self, cmd: AppendData) -> None:
        """Append a new data batch."""
        self._apply_event(
            AppendIngestionRequested(
                dataset=cmd.dataset,
                contract_id=cmd.contract_id,
                batch_id=cmd.batch_id,
                file_url=cmd.file_url,
                requested_at=datetime.now(UTC),
            )
        )
        self._apply_event(
            DataAppended(
                dataset=cmd.dataset,
                contract_id=cmd.contract_id,
                batch_id=cmd.batch_id,
                appended_at=datetime.now(UTC),
            )
        )

    def quarantine(self, cmd: QuarantineBatch) -> None:
        """Quarantine a batch."""
        self._apply_event(
            BatchQuarantined(
                batch_id=cmd.batch_id,
                reason=cmd.reason,
                quarantined_at=datetime.now(UTC),
            )
        )

    def release_quarantine(self, cmd: ReleaseQuarantine) -> None:
        """Release a batch from quarantine."""
        self._apply_event(
            QuarantineReleased(
                batch_id=cmd.batch_id,
                released_at=datetime.now(UTC),
            )
        )

    def publish(self, cmd: PublishData) -> None:
        """Publish a batch for consumption."""
        self._apply_event(
            DataPublished(
                batch_id=cmd.batch_id,
                published_at=datetime.now(UTC),
            )
        )


"""Anonymization job aggregate."""


@dataclass
class AnonymizationJob(AggregateRoot):
    """Aggregate managing anonymization job lifecycle."""

    table_schema: TableSchema | None = None
    rules: list[AnonymizationRule] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    requester: str = ""
    reason: str = ""
    dry_run_result: DryRunResult | None = None
    backup_location: str | None = None
    rows_affected: int = 0
    columns_affected: int = 0
    error_message: str | None = None

    def create(
        self,
        job_id: str,
        table_schema: TableSchema,
        rules: list[AnonymizationRule],
        requester: str,
        reason: str,
    ) -> None:
        """Create a new anonymization job."""
        if self.table_schema:
            msg = "Job already created"
            raise ValueError(msg)

        if not rules:
            msg = "At least one anonymization rule required"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AnonymizationJobCreated(
                job_id=job_id,
                table_schema=table_schema,
                rules=rules,
                requester=requester,
                reason=reason,
                created_at=now,
            )
        )

    def start_dry_run(self) -> None:
        """Start dry-run validation."""
        if self.status != JobStatus.PENDING:
            msg = f"Cannot start dry-run in status: {self.status}"
            raise ValueError(msg)

        if not self.table_schema:
            msg = "Table schema required for dry-run"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            DryRunStarted(
                job_id=self.aggregate_id,
                table_schema=self.table_schema,
                started_at=now,
            )
        )

    def complete_dry_run(self, result: DryRunResult) -> None:
        """Complete dry-run with results."""
        if self.status != JobStatus.DRY_RUN_STARTED:
            msg = f"Cannot complete dry-run in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            DryRunCompleted(job_id=self.aggregate_id, result=result, completed_at=now)
        )

    def fail_dry_run(self, reason: str) -> None:
        """Fail dry-run validation."""
        if self.status != JobStatus.DRY_RUN_STARTED:
            msg = f"Cannot fail dry-run in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(DryRunFailed(job_id=self.aggregate_id, reason=reason, failed_at=now))

    def approve(self, approver: str) -> None:
        """Approve job after successful dry-run."""
        if self.status != JobStatus.DRY_RUN_COMPLETED:
            msg = f"Cannot approve job in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            ValidationPassed(job_id=self.aggregate_id, approved_by=approver, approved_at=now)
        )

    def start_anonymization(self, backup_location: str) -> None:
        """Start actual anonymization."""
        if self.status != JobStatus.VALIDATION_PASSED:
            msg = f"Cannot start anonymization in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AnonymizationStarted(
                job_id=self.aggregate_id,
                backup_location=backup_location,
                started_at=now,
            )
        )

    def anonymize_column(self, column_name: str, strategy: str, rows_affected: int) -> None:
        """Record column anonymization."""
        if self.status != JobStatus.ANONYMIZATION_STARTED:
            msg = f"Cannot anonymize column in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        # Always pass strategy as str (enum.value if enum)
        strategy_str = str(strategy.value) if hasattr(strategy, "value") else str(strategy)
        self._apply_event(
            ColumnAnonymized(
                job_id=self.aggregate_id,
                column_name=column_name,
                strategy=strategy_str,
                rows_affected=rows_affected,
                anonymized_at=now,
            )
        )

    def complete_anonymization(self, total_rows: int, total_columns: int, duration: float) -> None:
        """Complete anonymization successfully."""
        if self.status != JobStatus.ANONYMIZATION_STARTED:
            msg = f"Cannot complete anonymization in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AnonymizationCompleted(
                job_id=self.aggregate_id,
                total_rows_affected=total_rows,
                total_columns_affected=total_columns,
                duration_seconds=duration,
                completed_at=now,
            )
        )

    def fail_anonymization(self, reason: str, column_name: str | None = None) -> None:
        """Fail anonymization."""
        if self.status != JobStatus.ANONYMIZATION_STARTED:
            msg = f"Cannot fail anonymization in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AnonymizationFailed(
                job_id=self.aggregate_id,
                reason=reason,
                column_name=column_name,
                failed_at=now,
            )
        )

    def rollback(self, backup_location: str) -> None:
        """Rollback anonymization from backup."""
        if self.status not in (
            JobStatus.ANONYMIZATION_FAILED,
            JobStatus.ANONYMIZATION_COMPLETED,
        ):
            msg = f"Cannot rollback in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(UTC)
        self._apply_event(
            AnonymizationRolledBack(
                job_id=self.aggregate_id,
                backup_restored_from=backup_location,
                rolled_back_at=now,
            )
        )

    # Event handlers

    def _when_anonymization_job_created(self, event: AnonymizationJobCreated) -> None:
        """Apply AnonymizationJobCreated event."""
        self.aggregate_id = event.job_id
        self.table_schema = event.table_schema
        self.rules = event.rules
        self.requester = event.requester
        self.reason = event.reason
        self.status = JobStatus.PENDING

    def _when_dry_run_started(self, _event: DryRunStarted) -> None:
        """Apply DryRunStarted event."""
        self.status = JobStatus.DRY_RUN_STARTED

    def _when_dry_run_completed(self, event: DryRunCompleted) -> None:
        """Apply DryRunCompleted event."""
        self.dry_run_result = event.result
        self.status = JobStatus.DRY_RUN_COMPLETED

    def _when_dry_run_failed(self, event: DryRunFailed) -> None:
        """Apply DryRunFailed event."""
        self.error_message = event.reason
        self.status = JobStatus.DRY_RUN_FAILED

    def _when_validation_passed(self, _event: ValidationPassed) -> None:
        """Apply ValidationPassed event."""
        self.status = JobStatus.VALIDATION_PASSED

    def _when_anonymization_started(self, event: AnonymizationStarted) -> None:
        """Apply AnonymizationStarted event."""
        self.backup_location = event.backup_location
        self.status = JobStatus.ANONYMIZATION_STARTED

    def _when_column_anonymized(self, event: ColumnAnonymized) -> None:
        """Apply ColumnAnonymized event."""
        self.columns_affected += 1
        self.rows_affected += event.rows_affected

    def _when_anonymization_completed(self, _event: AnonymizationCompleted) -> None:
        """Apply AnonymizationCompleted event."""
        self.status = JobStatus.ANONYMIZATION_COMPLETED

    def _when_anonymization_failed(self, event: AnonymizationFailed) -> None:
        """Apply AnonymizationFailed event."""
        self.error_message = event.reason
        self.status = JobStatus.ANONYMIZATION_FAILED

    def _when_anonymization_rolled_back(self, _event: AnonymizationRolledBack) -> None:
        """Apply AnonymizationRolledBack event."""
        self.status = JobStatus.ROLLED_BACK
