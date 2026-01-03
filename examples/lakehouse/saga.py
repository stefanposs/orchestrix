"""Anonymization saga coordinating dry-run and actual anonymization."""
import time
from dataclasses import dataclass

from orchestrix.core.aggregate import AggregateRepository
from orchestrix.core.messaging import MessageBus

from .aggregate import AnonymizationJob
from .engine import AnonymizationEngine, LakehouseTable
from .models import (
    AnonymizationFailed,
    AnonymizationJobCreated,
    ApproveJob,
    DryRunCompleted,
    DryRunResult,
    RollbackAnonymization,
    StartAnonymization,
    StartDryRun,
    ValidationPassed,
)


@dataclass
class AnonymizationSaga:
    """Saga coordinating the anonymization workflow."""

    message_bus: MessageBus
    repository: AggregateRepository
    lakehouse_tables: dict[str, LakehouseTable]
    engine: AnonymizationEngine

    async def handle_job_created(self, event: AnonymizationJobCreated) -> None:
        """Automatically start dry-run when job is created."""
        print(f"\n📋 Job created: {event.job_id}")
        print(f"   Table: {event.table_schema.database}.{event.table_schema.schema_name}.{event.table_schema.table_name}")
        print(f"   Rules: {len(event.rules)} anonymization rules")
        print(f"   Requester: {event.requester}")
        print(f"   Reason: {event.reason}")

        # Automatically start dry-run
        await self.message_bus.publish_async(StartDryRun(job_id=event.job_id))

    async def handle_start_dry_run(self, command: StartDryRun) -> None:
        """Execute dry-run validation."""
        # Load job
        job = await self.repository.load_async(AnonymizationJob, command.job_id)
        job.start_dry_run()
        await self.repository.save_async(job)

        # Publish events
        for evt in job.uncommitted_events:
            await self.message_bus.publish_async(evt.data)

        print(f"\n🧪 Dry-run started for job {command.job_id}")

        # Execute dry-run (simulated)
        try:
            table_key = f"{job.table_schema.database}.{job.table_schema.schema_name}.{job.table_schema.table_name}"
            table = self.lakehouse_tables.get(table_key)

            if not table:
                msg = f"Table not found: {table_key}"
                raise ValueError(msg)

            # Get sample before
            sample_before = {
                col: [row.get(col) for row in table.get_sample()]
                for col in job.table_schema.columns[:5]
            }

            # Simulate anonymization on copy
            test_data = [row.copy() for row in table.data]
            test_table = LakehouseTable(
                database=table.database,
                schema_name=table.schema_name,
                table_name=f"{table.table_name}_test",
                data=test_data,
            )

            affected_columns = []
            total_affected_rows = 0
            warnings = []

            for rule in job.rules:
                print(f"   - Testing {rule.column_name}: {rule.strategy.value}")

                if rule.column_name not in job.table_schema.columns:
                    warnings.append(f"Column {rule.column_name} not found in table")
                    continue

                rows = test_table.anonymize_column(
                    column_name=rule.column_name,
                    engine=self.engine,
                    strategy_name=rule.strategy.value,
                    preserve_format=rule.preserve_format,
                    preserve_null=rule.preserve_null,
                    value_type=rule.column_type.value,
                )

                affected_columns.append(rule.column_name)
                total_affected_rows = max(total_affected_rows, rows)

            # Get sample after
            sample_after = {
                col: [row.get(col) for row in test_table.get_sample()]
                for col in job.table_schema.columns[:5]
            }

            # Estimate duration
            estimated_duration = len(job.rules) * 0.1  # 0.1s per rule

            result = DryRunResult(
                affected_rows=total_affected_rows,
                affected_columns=affected_columns,
                estimated_duration_seconds=estimated_duration,
                warnings=warnings,
                sample_before=sample_before,
                sample_after=sample_after,
            )

            # Complete dry-run
            job = await self.repository.load_async(AnonymizationJob, command.job_id)
            job.complete_dry_run(result)
            await self.repository.save_async(job)

            # Publish events
            for evt in job.uncommitted_events:
                await self.message_bus.publish_async(evt)

            print(f"✅ Dry-run completed")
            print(f"   Affected rows: {result.affected_rows}")
            print(f"   Affected columns: {len(result.affected_columns)}")
            if warnings:
                print(f"   ⚠️  Warnings: {len(warnings)}")

        except Exception as e:
            # Fail dry-run
            job = await self.repository.load_async(AnonymizationJob, command.job_id)
            job.fail_dry_run(str(e))
            await self.repository.save_async(job)

            # Publish events
            for evt in job.uncommitted_events:
                await self.message_bus.publish_async(evt)

            print(f"❌ Dry-run failed: {e}")

    async def handle_dry_run_completed(self, event: DryRunCompleted) -> None:
        """Show dry-run results and wait for approval."""
        print(f"\n📊 Dry-Run Results:")
        print(f"   Estimated duration: {event.result.estimated_duration_seconds:.2f}s")
        print(f"   Affected rows: {event.result.affected_rows}")
        print(f"   Affected columns: {', '.join(event.result.affected_columns)}")

        if event.result.warnings:
            print(f"\n   ⚠️  Warnings:")
            for warning in event.result.warnings:
                print(f"      - {warning}")

        print(f"\n   Sample Preview:")
        for col in list(event.result.sample_before.keys())[:3]:
            before = event.result.sample_before[col]
            after = event.result.sample_after[col]
            print(f"   {col}:")
            print(f"      Before: {before[:3]}")
            print(f"      After:  {after[:3]}")

        print(f"\n✅ Dry-run passed! Ready for approval.")

        # Auto-approve for demo (in production, wait for manual approval)
        await self.message_bus.publish_async(
            ApproveJob(job_id=event.job_id, approver="system")
        )

    async def handle_approve_job(self, command: ApproveJob) -> None:
        """Approve job and start anonymization."""
        # Load and approve job
        job = await self.repository.load_async(AnonymizationJob, command.job_id)
        job.approve(command.approver)
        await self.repository.save_async(job)

        # Publish events
        for evt in job.uncommitted_events:
            await self.message_bus.publish_async(evt)

        print(f"\n✓ Job approved by {command.approver}")

        # Automatically start anonymization
        await self.message_bus.publish_async(StartAnonymization(job_id=command.job_id))

    async def handle_validation_passed(self, event: ValidationPassed) -> None:
        """Log validation passed."""
        print(f"✓ Validation passed, approved by {event.approved_by}")

    async def handle_start_anonymization(self, command: StartAnonymization) -> None:
        """Execute actual anonymization."""
        # Load job
        job = await self.repository.load_async(AnonymizationJob, command.job_id)

        # Get table
        table_key = f"{job.table_schema.database}.{job.table_schema.schema_name}.{job.table_schema.table_name}"
        table = self.lakehouse_tables.get(table_key)

        if not table:
            msg = f"Table not found: {table_key}"
            raise ValueError(msg)

        # Create backup
        backup_location = table.backup()
        job.start_anonymization(backup_location)
        await self.repository.save_async(job)

        # Publish events
        for evt in job.uncommitted_events:
            await self.message_bus.publish_async(evt)

        print(f"\n🔒 Anonymization started")
        print(f"   Backup created: {backup_location}")

        # Execute anonymization
        start_time = time.time()

        try:
            for rule in job.rules:
                print(f"   - Anonymizing {rule.column_name} with {rule.strategy.value}...")

                rows_affected = table.anonymize_column(
                    column_name=rule.column_name,
                    engine=self.engine,
                    strategy_name=rule.strategy.value,
                    preserve_format=rule.preserve_format,
                    preserve_null=rule.preserve_null,
                    value_type=rule.column_type.value,
                )

                # Record column anonymization
                job = await self.repository.load_async(
                    AnonymizationJob, command.job_id
                )
                job.anonymize_column(
                    column_name=rule.column_name,
                    strategy=rule.strategy.value,
                    rows_affected=rows_affected,
                )
                await self.repository.save_async(job)

                # Publish events
                for evt in job.uncommitted_events:
                    await self.message_bus.publish_async(evt)

            duration = time.time() - start_time

            # Complete anonymization
            job = await self.repository.load_async(AnonymizationJob, command.job_id)
            job.complete_anonymization(
                total_rows=job.rows_affected,
                total_columns=job.columns_affected,
                duration=duration,
            )
            await self.repository.save_async(job)

            # Publish events
            for evt in job.uncommitted_events:
                await self.message_bus.publish_async(evt)

            print(f"\n✅ Anonymization completed successfully!")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Total rows affected: {job.rows_affected}")
            print(f"   Total columns affected: {job.columns_affected}")

        except Exception as e:
            # Fail anonymization
            job = await self.repository.load_async(AnonymizationJob, command.job_id)
            job.fail_anonymization(str(e))
            await self.repository.save_async(job)

            # Publish events
            for evt in job.uncommitted_events:
                await self.message_bus.publish_async(evt)

            print(f"\n❌ Anonymization failed: {e}")
            print(f"   Initiating rollback...")

            # Trigger rollback
            await self.message_bus.publish_async(
                RollbackAnonymization(job_id=command.job_id)
            )

    async def handle_anonymization_failed(self, event: AnonymizationFailed) -> None:
        """Handle anonymization failure."""
        print(f"\n❌ Anonymization failed for job {event.job_id}")
        print(f"   Reason: {event.reason}")
        if event.column_name:
            print(f"   Failed column: {event.column_name}")

    async def handle_rollback_anonymization(self, command: RollbackAnonymization) -> None:
        """Rollback anonymization from backup."""
        # Load job
        job = await self.repository.load_async(AnonymizationJob, command.job_id)

        # Get table
        table_key = f"{job.table_schema.database}.{job.table_schema.schema_name}.{job.table_schema.table_name}"
        table = self.lakehouse_tables.get(table_key)

        if table and job.backup_location:
            # Restore from backup
            table.restore()
            print(f"♻️  Restored from backup: {job.backup_location}")

            # Record rollback
            job.rollback(job.backup_location)
            await self.repository.save_async(job)

            # Publish events
            for evt in job.uncommitted_events:
                await self.message_bus.publish_async(evt)

            print(f"✅ Rollback completed")


def register_saga(
    message_bus: MessageBus,
    repository: AggregateRepository,
    lakehouse_tables: dict[str, LakehouseTable],
    engine: AnonymizationEngine,
) -> AnonymizationSaga:
    """Register saga with message bus."""
    saga = AnonymizationSaga(
        message_bus=message_bus,
        repository=repository,
        lakehouse_tables=lakehouse_tables,
        engine=engine,
    )

    # Subscribe to events
    message_bus.subscribe(AnonymizationJobCreated, saga.handle_job_created)
    message_bus.subscribe(DryRunCompleted, saga.handle_dry_run_completed)
    message_bus.subscribe(ValidationPassed, saga.handle_validation_passed)
    message_bus.subscribe(AnonymizationFailed, saga.handle_anonymization_failed)

    # Subscribe to commands
    message_bus.subscribe(StartDryRun, saga.handle_start_dry_run)
    message_bus.subscribe(ApproveJob, saga.handle_approve_job)
    message_bus.subscribe(StartAnonymization, saga.handle_start_anonymization)
    message_bus.subscribe(RollbackAnonymization, saga.handle_rollback_anonymization)

    return saga
