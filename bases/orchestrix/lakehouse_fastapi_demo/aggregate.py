from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
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
    CheckSLA,
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
    DefineSLA,
    DeprecateDataset,
    DryRunCompleted,
    DryRunFailed,
    DryRunResult,
    DryRunStarted,
    ExecutionCompleted,
    ExecutionFailed,
    ExecutionStarted,
    JobStatus,
    PrivacyCheckPassed,
    PublishData,
    QualityCheckPassed,
    QuarantineBatch,
    QuarantineReleased,
    RegisterDataset,
    ReleaseQuarantine,
    RequestExecution,
    SLABreached,
    SLACheckPassed,
    SLADefined,
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
    dataset_version: str | None = None
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
        if self.deprecated:
            raise ValueError("Dataset already deprecated")
        self._apply_event(
            DatasetDeprecated(
                name=cmd.name,
                deprecated_at=datetime.now(UTC),
            )
        )

    # Event handlers — reconstruct state from events

    def _when_dataset_registered(self, event: DatasetRegistered) -> None:
        self.name = event.name
        self.schema = event.schema
        self.description = event.description
        self.registered_at = event.registered_at

    def _when_dataset_version_activated(self, event: DatasetVersionActivated) -> None:
        self.dataset_version = event.version

    def _when_dataset_deprecated(self, _event: DatasetDeprecated) -> None:
        self.deprecated = True


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

    # Event handlers — reconstruct state from events

    def _when_data_contract_defined(self, event: DataContractDefined) -> None:
        self.contract_id = event.contract_id
        self.dataset = event.dataset
        self.schema = event.schema
        self.privacy_rules = event.privacy_rules
        self.quality_rules = event.quality_rules
        self.defined_at = event.defined_at

    def _when_data_contract_approved(self, event: DataContractApproved) -> None:
        self.approved = True
        self.approved_at = event.approved_at

    def _when_data_contract_deprecated(self, _event: DataContractDeprecated) -> None:
        self.deprecated = True

    def _when_data_contract_updated(self, _event: DataContractUpdated) -> None:
        pass  # Schema updates handled via new contract version


# --- Batch Aggregate ---


class BatchStatus(Enum):
    """Lifecycle states of a data batch."""

    INGESTED = "ingested"
    QUARANTINED = "quarantined"
    VALIDATED = "validated"
    PUBLISHED = "published"


@dataclass
class BatchAggregate(AggregateRoot):
    """Aggregate for batch (data ingestion) lifecycle.

    State machine::

        INGESTED → QUARANTINED → (released) → INGESTED
                 → VALIDATED (after DQ + privacy pass)
                 → PUBLISHED (after validation)
    """

    batch_id: str = ""
    dataset: str = ""
    contract_id: str = ""
    file_url: str | None = None
    status: BatchStatus = BatchStatus.INGESTED
    quarantined: bool = False
    published: bool = False
    dq_passed: bool = False
    privacy_passed: bool = False
    quarantine_reason: str | None = None

    # --- Commands with lifecycle guards ---

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
        """Quarantine a batch — only if not already published."""
        if self.status == BatchStatus.PUBLISHED:
            raise ValueError("Cannot quarantine a published batch")
        self._apply_event(
            BatchQuarantined(
                batch_id=cmd.batch_id,
                reason=cmd.reason,
                quarantined_at=datetime.now(UTC),
            )
        )

    def release_quarantine(self, cmd: ReleaseQuarantine) -> None:
        """Release from quarantine — only if currently quarantined."""
        if self.status != BatchStatus.QUARANTINED:
            raise ValueError("Batch is not quarantined")
        self._apply_event(
            QuarantineReleased(
                batch_id=cmd.batch_id,
                released_at=datetime.now(UTC),
            )
        )

    def mark_dq_passed(self, batch_id: str) -> None:
        """Mark DQ check as passed. Emits *QualityCheckPassed*."""
        if self.status not in (BatchStatus.INGESTED, BatchStatus.VALIDATED):
            raise ValueError(f"Cannot run DQ check in status: {self.status.value}")
        self._apply_event(QualityCheckPassed(batch_id=batch_id, checked_at=datetime.now(UTC)))

    def mark_privacy_passed(self, batch_id: str) -> None:
        """Mark privacy check as passed. Emits *PrivacyCheckPassed*."""
        if self.status not in (BatchStatus.INGESTED, BatchStatus.VALIDATED):
            raise ValueError(f"Cannot run privacy check in status: {self.status.value}")
        self._apply_event(PrivacyCheckPassed(batch_id=batch_id, checked_at=datetime.now(UTC)))

    def _check_validation_complete(self) -> None:
        """Transition to VALIDATED if both checks passed."""
        if self.dq_passed and self.privacy_passed:
            self.status = BatchStatus.VALIDATED

    def publish(self, cmd: PublishData) -> None:
        """Publish a batch — requires VALIDATED or INGESTED status."""
        if self.status == BatchStatus.QUARANTINED:
            raise ValueError("Cannot publish a quarantined batch")
        if self.status == BatchStatus.PUBLISHED:
            raise ValueError("Batch is already published")
        self._apply_event(
            DataPublished(
                batch_id=cmd.batch_id,
                published_at=datetime.now(UTC),
            )
        )

    # --- Event handlers — reconstruct state from events ---

    def _when_append_ingestion_requested(self, event: AppendIngestionRequested) -> None:
        self.batch_id = event.batch_id
        self.dataset = event.dataset
        self.contract_id = event.contract_id
        self.file_url = event.file_url

    def _when_data_appended(self, _event: DataAppended) -> None:
        self.status = BatchStatus.INGESTED

    def _when_batch_quarantined(self, event: BatchQuarantined) -> None:
        self.status = BatchStatus.QUARANTINED
        self.quarantined = True
        self.quarantine_reason = event.reason

    def _when_quarantine_released(self, _event: QuarantineReleased) -> None:
        self.status = BatchStatus.INGESTED
        self.quarantined = False
        self.quarantine_reason = None

    def _when_data_published(self, _event: DataPublished) -> None:
        self.status = BatchStatus.PUBLISHED
        self.published = True

    def _when_quality_check_passed(self, _event: QualityCheckPassed) -> None:
        self.dq_passed = True
        self._check_validation_complete()

    def _when_privacy_check_passed(self, _event: PrivacyCheckPassed) -> None:
        self.privacy_passed = True
        self._check_validation_complete()


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


# --- SLA Aggregate ---


@dataclass
class SLAAggregate(AggregateRoot):
    """Aggregate for SLA enforcement and monitoring."""

    sla_id: str = ""
    dataset: str = ""
    freshness_hours: float = 0.0
    availability_pct: float = 99.9
    owner: str = ""
    consumers: list[str] = field(default_factory=list)
    breached: bool = False
    last_check_passed: bool | None = None
    breach_count: int = 0
    defined_at: datetime | None = None
    last_checked_at: datetime | None = None

    def define(self, cmd: DefineSLA) -> None:
        """Define SLA for a dataset."""
        if self.sla_id:
            raise ValueError("SLA already defined")
        self._apply_event(
            SLADefined(
                dataset=cmd.dataset,
                sla_id=self.aggregate_id,
                freshness_hours=cmd.freshness_hours,
                availability_pct=cmd.availability_pct,
                owner=cmd.owner,
                consumers=cmd.consumers,
                defined_at=datetime.now(UTC),
            )
        )

    def check(self, cmd: CheckSLA, freshness_ok: bool, availability_ok: bool) -> None:
        """Run an SLA check — pass or breach."""
        if freshness_ok and availability_ok:
            self._apply_event(
                SLACheckPassed(
                    sla_id=self.aggregate_id,
                    dataset=self.dataset,
                    freshness_ok=freshness_ok,
                    availability_ok=availability_ok,
                    checked_at=datetime.now(UTC),
                )
            )
        else:
            violations = []
            if not freshness_ok:
                violations.append(f"freshness > {self.freshness_hours}h")
            if not availability_ok:
                violations.append(f"availability < {self.availability_pct}%")
            self._apply_event(
                SLABreached(
                    sla_id=self.aggregate_id,
                    dataset=self.dataset,
                    violation="; ".join(violations),
                    breached_at=datetime.now(UTC),
                )
            )

    def _when_sla_defined(self, event: SLADefined) -> None:
        self.sla_id = event.sla_id
        self.dataset = event.dataset
        self.freshness_hours = event.freshness_hours
        self.availability_pct = event.availability_pct
        self.owner = event.owner
        self.consumers = list(event.consumers)
        self.defined_at = event.defined_at

    def _when_sla_check_passed(self, event: SLACheckPassed) -> None:
        self.last_check_passed = True
        self.breached = False
        self.last_checked_at = event.checked_at

    def _when_sla_breached(self, event: SLABreached) -> None:
        self.breached = True
        self.last_check_passed = False
        self.breach_count += 1
        self.last_checked_at = event.breached_at


# --- Execution Job Aggregate ---


class ExecutionStatus(Enum):
    """Lifecycle states of an execution job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionJobAggregate(AggregateRoot):
    """Aggregate for executor job lifecycle."""

    job_id: str = ""
    job_type: str = ""
    dataset: str = ""
    batch_id: str = ""
    executor_type: str = "local_python"
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_seconds: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def request(self, cmd: RequestExecution) -> None:
        """Start an execution job."""
        if self.status != ExecutionStatus.PENDING:
            raise ValueError(f"Cannot start job in status: {self.status.value}")
        self._apply_event(
            ExecutionStarted(
                job_id=cmd.job_id,
                job_type=cmd.job_type,
                dataset=cmd.dataset,
                batch_id=cmd.batch_id,
                executor_type=cmd.executor_type,
                started_at=datetime.now(UTC),
            )
        )

    def complete(self, result: dict[str, Any], duration: float) -> None:
        """Mark job as completed."""
        if self.status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot complete job in status: {self.status.value}")
        self._apply_event(
            ExecutionCompleted(
                job_id=self.aggregate_id,
                job_type=self.job_type,
                dataset=self.dataset,
                batch_id=self.batch_id,
                result=result,
                duration_seconds=duration,
                completed_at=datetime.now(UTC),
            )
        )

    def fail(self, reason: str) -> None:
        """Mark job as failed."""
        if self.status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot fail job in status: {self.status.value}")
        self._apply_event(
            ExecutionFailed(
                job_id=self.aggregate_id,
                job_type=self.job_type,
                dataset=self.dataset,
                batch_id=self.batch_id,
                reason=reason,
                failed_at=datetime.now(UTC),
            )
        )

    def _when_execution_started(self, event: ExecutionStarted) -> None:
        self.job_id = event.job_id
        self.job_type = event.job_type
        self.dataset = event.dataset
        self.batch_id = event.batch_id
        self.executor_type = event.executor_type
        self.status = ExecutionStatus.RUNNING
        self.started_at = event.started_at

    def _when_execution_completed(self, event: ExecutionCompleted) -> None:
        self.status = ExecutionStatus.COMPLETED
        self.result = event.result
        self.duration_seconds = event.duration_seconds
        self.completed_at = event.completed_at

    def _when_execution_failed(self, event: ExecutionFailed) -> None:
        self.status = ExecutionStatus.FAILED
        self.error = event.reason
