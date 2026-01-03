"""Anonymization job aggregate."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from orchestrix.core.aggregate import AggregateRoot
from orchestrix.core.event import Event

from .models import (
    AnonymizationCompleted,
    AnonymizationFailed,
    AnonymizationJobCreated,
    AnonymizationRule,
    AnonymizationRolledBack,
    AnonymizationStarted,
    ColumnAnonymized,
    DryRunCompleted,
    DryRunFailed,
    DryRunResult,
    DryRunStarted,
    JobStatus,
    TableSchema,
    ValidationPassed,
)


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

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AnonymizationJobCreated",
                AnonymizationJobCreated(
                    job_id=job_id,
                    table_schema=table_schema,
                    rules=rules,
                    requester=requester,
                    reason=reason,
                    created_at=now,
                ),
            )
        )

    def start_dry_run(self) -> None:
        """Start dry-run validation."""
        if self.status != JobStatus.PENDING:
            msg = f"Cannot start dry-run in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "DryRunStarted",
                DryRunStarted(
                    job_id=self.id,
                    table_schema=self.table_schema,
                    started_at=now,
                ),
            )
        )

    def complete_dry_run(self, result: DryRunResult) -> None:
        """Complete dry-run with results."""
        if self.status != JobStatus.DRY_RUN_STARTED:
            msg = f"Cannot complete dry-run in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "DryRunCompleted",
                DryRunCompleted(
                    job_id=self.id, result=result, completed_at=now
                ),
            )
        )

    def fail_dry_run(self, reason: str) -> None:
        """Fail dry-run validation."""
        if self.status != JobStatus.DRY_RUN_STARTED:
            msg = f"Cannot fail dry-run in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "DryRunFailed",
                DryRunFailed(job_id=self.id, reason=reason, failed_at=now),
            )
        )

    def approve(self, approver: str) -> None:
        """Approve job after successful dry-run."""
        if self.status != JobStatus.DRY_RUN_COMPLETED:
            msg = f"Cannot approve job in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "ValidationPassed",
                ValidationPassed(
                    job_id=self.id, approved_by=approver, approved_at=now
                ),
            )
        )

    def start_anonymization(self, backup_location: str) -> None:
        """Start actual anonymization."""
        if self.status != JobStatus.VALIDATION_PASSED:
            msg = f"Cannot start anonymization in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AnonymizationStarted",
                AnonymizationStarted(
                    job_id=self.id,
                    backup_location=backup_location,
                    started_at=now,
                ),
            )
        )

    def anonymize_column(
        self, column_name: str, strategy: str, rows_affected: int
    ) -> None:
        """Record column anonymization."""
        if self.status != JobStatus.ANONYMIZATION_STARTED:
            msg = f"Cannot anonymize column in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "ColumnAnonymized",
                ColumnAnonymized(
                    job_id=self.id,
                    column_name=column_name,
                    strategy=strategy,
                    rows_affected=rows_affected,
                    anonymized_at=now,
                ),
            )
        )

    def complete_anonymization(
        self, total_rows: int, total_columns: int, duration: float
    ) -> None:
        """Complete anonymization successfully."""
        if self.status != JobStatus.ANONYMIZATION_STARTED:
            msg = f"Cannot complete anonymization in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AnonymizationCompleted",
                AnonymizationCompleted(
                    job_id=self.id,
                    total_rows_affected=total_rows,
                    total_columns_affected=total_columns,
                    duration_seconds=duration,
                    completed_at=now,
                ),
            )
        )

    def fail_anonymization(self, reason: str, column_name: str | None = None) -> None:
        """Fail anonymization."""
        if self.status != JobStatus.ANONYMIZATION_STARTED:
            msg = f"Cannot fail anonymization in status: {self.status}"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AnonymizationFailed",
                AnonymizationFailed(
                    job_id=self.id,
                    reason=reason,
                    column_name=column_name,
                    failed_at=now,
                ),
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

        now = datetime.now(timezone.utc)
        self._apply_event(
            Event.from_aggregate(
                self,
                "AnonymizationRolledBack",
                AnonymizationRolledBack(
                    job_id=self.id,
                    backup_restored_from=backup_location,
                    rolled_back_at=now,
                ),
            )
        )

    # Event handlers

    def _when_anonymization_job_created(self, event: Event) -> None:
        """Apply AnonymizationJobCreated event."""
        data = event.data
        self.id = data.job_id
        self.table_schema = data.table_schema
        self.rules = data.rules
        self.requester = data.requester
        self.reason = data.reason
        self.status = JobStatus.PENDING

    def _when_dry_run_started(self, _event: Event) -> None:
        """Apply DryRunStarted event."""
        self.status = JobStatus.DRY_RUN_STARTED

    def _when_dry_run_completed(self, event: Event) -> None:
        """Apply DryRunCompleted event."""
        data = event.data
        self.dry_run_result = data.result
        self.status = JobStatus.DRY_RUN_COMPLETED

    def _when_dry_run_failed(self, event: Event) -> None:
        """Apply DryRunFailed event."""
        data = event.data
        self.error_message = data.reason
        self.status = JobStatus.DRY_RUN_FAILED

    def _when_validation_passed(self, _event: Event) -> None:
        """Apply ValidationPassed event."""
        self.status = JobStatus.VALIDATION_PASSED

    def _when_anonymization_started(self, event: Event) -> None:
        """Apply AnonymizationStarted event."""
        data = event.data
        self.backup_location = data.backup_location
        self.status = JobStatus.ANONYMIZATION_STARTED

    def _when_column_anonymized(self, event: Event) -> None:
        """Apply ColumnAnonymized event."""
        data = event.data
        self.columns_affected += 1
        self.rows_affected += data.rows_affected

    def _when_anonymization_completed(self, _event: Event) -> None:
        """Apply AnonymizationCompleted event."""
        self.status = JobStatus.ANONYMIZATION_COMPLETED

    def _when_anonymization_failed(self, event: Event) -> None:
        """Apply AnonymizationFailed event."""
        data = event.data
        self.error_message = data.reason
        self.status = JobStatus.ANONYMIZATION_FAILED

    def _when_anonymization_rolled_back(self, _event: Event) -> None:
        """Apply AnonymizationRolledBack event."""
        self.status = JobStatus.ROLLED_BACK
