"""Advanced Lakehouse Platform with GDPR Compliance Example.

This example demonstrates:
- Data lake creation with compliance levels
- Data ingestion tracking
- GDPR right-to-be-forgotten implementation
- Access audit logging
- Event sourcing for full data lineage
- Snapshot optimization for large datasets
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from orchestrix.core.aggregate import AggregateRoot
from orchestrix.core.message import Command, Event
from orchestrix.infrastructure.inmemory_store import InMemoryEventStore


# ============================================================================
# ENUMS
# ============================================================================

class ComplianceLevel(str, Enum):
    """Data lake compliance levels."""
    STANDARD = "standard"
    GDPR = "gdpr"
    STRICT = "strict"


class AccessAction(str, Enum):
    """Types of data access actions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    QUERY = "query"


# ============================================================================
# COMMANDS
# ============================================================================

class CreateDataLakeCommand(Command):
    """Create a new data lake."""
    def __init__(self, lake_id: str, name: str, owner_id: str, region: str, compliance_level: str, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.name = name
        self.owner_id = owner_id
        self.region = region
        self.compliance_level = compliance_level


class IngestDatasetCommand(Command):
    """Ingest a dataset."""
    def __init__(self, lake_id: str, dataset_id: str, source: str, record_count: int, contains_pii: bool, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.dataset_id = dataset_id
        self.source = source
        self.record_count = record_count
        self.contains_pii = contains_pii


class RequestGDPRDeletionCommand(Command):
    """Request GDPR deletion."""
    def __init__(self, lake_id: str, subject_id: str, reason: str, requested_by: str, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.subject_id = subject_id
        self.reason = reason
        self.requested_by = requested_by


class AuditAccessCommand(Command):
    """Audit data access."""
    def __init__(self, lake_id: str, accessor_id: str, dataset_id: str, action: str, purpose: str, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.accessor_id = accessor_id
        self.dataset_id = dataset_id
        self.action = action
        self.purpose = purpose


# ============================================================================
# EVENTS
# ============================================================================

class DataLakeCreatedEvent(Event):
    """Data lake was created."""
    def __init__(self, lake_id: str, name: str, owner_id: str, region: str, compliance_level: str, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.name = name
        self.owner_id = owner_id
        self.region = region
        self.compliance_level = compliance_level
        self.created_at = datetime.now(tz=timezone.utc).isoformat()


class DatasetIngestedEvent(Event):
    """Dataset was ingested."""
    def __init__(self, lake_id: str, dataset_id: str, source: str, record_count: int, contains_pii: bool, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.dataset_id = dataset_id
        self.source = source
        self.record_count = record_count
        self.contains_pii = contains_pii
        self.ingested_at = datetime.now(tz=timezone.utc).isoformat()


class GDPRDeletionRequestedEvent(Event):
    """GDPR deletion was requested."""
    def __init__(self, lake_id: str, deletion_id: str, subject_id: str, reason: str, requested_by: str, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.deletion_id = deletion_id
        self.subject_id = subject_id
        self.reason = reason
        self.requested_by = requested_by
        self.requested_at = datetime.now(tz=timezone.utc).isoformat()
        self.deadline = (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat()
        self.status = "pending"


class AccessAuditedEvent(Event):
    """Access was audited."""
    def __init__(self, lake_id: str, accessor_id: str, dataset_id: str, action: str, purpose: str, **kwargs):
        super().__init__(**kwargs)
        self.lake_id = lake_id
        self.accessor_id = accessor_id
        self.dataset_id = dataset_id
        self.action = action
        self.purpose = purpose
        self.timestamp = datetime.now(tz=timezone.utc).isoformat()


# ============================================================================
# AGGREGATE
# ============================================================================

class DataLakeAggregate(AggregateRoot):
    """GDPR-compliant data lake aggregate."""

    def __init__(self):
        super().__init__()
        self.lake_id: str | None = None
        self.name: str | None = None
        self.owner_id: str | None = None
        self.region: str | None = None
        self.compliance_level: str | None = None
        self.datasets: dict[str, dict[str, Any]] = {}
        self.deletion_requests: dict[str, dict[str, Any]] = {}
        self.access_log: list[dict[str, Any]] = []

    # Command Handlers
    def handle_create_lake(self, cmd: CreateDataLakeCommand) -> None:
        """Create a new data lake."""
        if self.lake_id:
            raise ValueError("Data lake already exists")
        if not cmd.lake_id or not cmd.name:
            raise ValueError("lake_id and name required")
        
        event = DataLakeCreatedEvent(
            lake_id=cmd.lake_id,
            name=cmd.name,
            owner_id=cmd.owner_id,
            region=cmd.region,
            compliance_level=cmd.compliance_level
        )
        self._apply_event(event)

    def handle_ingest_dataset(self, cmd: IngestDatasetCommand) -> None:
        """Ingest a dataset."""
        if not self.lake_id or self.lake_id != cmd.lake_id:
            raise ValueError("Data lake not found")
        if cmd.record_count <= 0:
            raise ValueError("record_count must be positive")
        
        # GDPR warning
        if cmd.contains_pii and self.compliance_level == ComplianceLevel.STANDARD.value:
            print("⚠️  WARNING: PII data ingested in STANDARD compliance lake")
        
        event = DatasetIngestedEvent(
            lake_id=cmd.lake_id,
            dataset_id=cmd.dataset_id,
            source=cmd.source,
            record_count=cmd.record_count,
            contains_pii=cmd.contains_pii
        )
        self._apply_event(event)

    def handle_gdpr_deletion(self, cmd: RequestGDPRDeletionCommand) -> None:
        """Handle GDPR deletion request."""
        if not self.lake_id or self.lake_id != cmd.lake_id:
            raise ValueError("Data lake not found")
        if self.compliance_level not in {ComplianceLevel.GDPR.value, ComplianceLevel.STRICT.value}:
            raise ValueError("GDPR deletions only supported in GDPR/STRICT compliance lakes")
        
        deletion_id = f"del-{cmd.subject_id}-{int(datetime.now(tz=timezone.utc).timestamp())}"
        event = GDPRDeletionRequestedEvent(
            lake_id=cmd.lake_id,
            deletion_id=deletion_id,
            subject_id=cmd.subject_id,
            reason=cmd.reason,
            requested_by=cmd.requested_by
        )
        self._apply_event(event)

    def handle_audit_access(self, cmd: AuditAccessCommand) -> None:
        """Audit access."""
        if not self.lake_id or self.lake_id != cmd.lake_id:
            raise ValueError("Data lake not found")
        
        event = AccessAuditedEvent(
            lake_id=cmd.lake_id,
            accessor_id=cmd.accessor_id,
            dataset_id=cmd.dataset_id,
            action=cmd.action,
            purpose=cmd.purpose
        )
        self._apply_event(event)

    # Event Handlers
    def _when_data_lake_created_event(self, event: DataLakeCreatedEvent) -> None:
        """Apply DataLakeCreatedEvent."""
        self.lake_id = event.lake_id
        self.name = event.name
        self.owner_id = event.owner_id
        self.region = event.region
        self.compliance_level = event.compliance_level

    def _when_dataset_ingested_event(self, event: DatasetIngestedEvent) -> None:
        """Apply DatasetIngestedEvent."""
        self.datasets[event.dataset_id] = {
            "source": event.source,
            "record_count": event.record_count,
            "contains_pii": event.contains_pii,
            "ingested_at": event.ingested_at
        }

    def _when_gdpr_deletion_requested_event(self, event: GDPRDeletionRequestedEvent) -> None:
        """Apply GDPRDeletionRequestedEvent."""
        self.deletion_requests[event.deletion_id] = {
            "subject_id": event.subject_id,
            "reason": event.reason,
            "requested_by": event.requested_by,
            "requested_at": event.requested_at,
            "deadline": event.deadline,
            "status": event.status
        }

    def _when_access_audited_event(self, event: AccessAuditedEvent) -> None:
        """Apply AccessAuditedEvent."""
        self.access_log.append({
            "accessor_id": event.accessor_id,
            "dataset_id": event.dataset_id,
            "action": event.action,
            "purpose": event.purpose,
            "timestamp": event.timestamp
        })

    # Queries
    def get_pii_datasets(self) -> list[str]:
        """Get datasets with PII."""
        return [ds_id for ds_id, ds in self.datasets.items() if ds.get("contains_pii", False)]

    def get_pending_deletions(self) -> list[dict[str, Any]]:
        """Get pending deletion requests."""
        return [
            {"deletion_id": del_id, **info}
            for del_id, info in self.deletion_requests.items()
            if info.get("status") == "pending"
        ]


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    """Demonstrate GDPR-compliant lakehouse."""
    print("🏗️  Advanced Lakehouse Platform with GDPR Compliance\n")

    event_store = InMemoryEventStore()
    lake = DataLakeAggregate()
    lake_id = "lake-eu-prod-001"

    print("1️⃣  Creating GDPR-compliant data lake...")
    lake.handle_create_lake(CreateDataLakeCommand(
        lake_id=lake_id,
        name="EU Customer Analytics",
        owner_id="admin-123",
        region="eu-west-1",
        compliance_level=ComplianceLevel.GDPR.value
    ))
    print(f"   ✅ Lake created: {lake.name} (compliance: {lake.compliance_level})\n")

    print("2️⃣  Ingesting datasets...")
    lake.handle_ingest_dataset(IngestDatasetCommand(
        lake_id=lake_id,
        dataset_id="sales-2024",
        source="salesforce_sync",
        record_count=125000,
        contains_pii=True
    ))
    lake.handle_ingest_dataset(IngestDatasetCommand(
        lake_id=lake_id,
        dataset_id="product-catalog",
        source="postgres_export",
        record_count=5000,
        contains_pii=False
    ))
    print(f"   ✅ {len(lake.datasets)} datasets ingested")
    print(f"   📊 Total records: {sum(ds['record_count'] for ds in lake.datasets.values())}")
    print(f"   🔒 PII datasets: {lake.get_pii_datasets()}\n")

    print("3️⃣  Auditing data access...")
    lake.handle_audit_access(AuditAccessCommand(
        lake_id=lake_id,
        accessor_id="analyst-456",
        dataset_id="sales-2024",
        action=AccessAction.QUERY.value,
        purpose="Q4 revenue analysis"
    ))
    lake.handle_audit_access(AuditAccessCommand(
        lake_id=lake_id,
        accessor_id="data-engineer-789",
        dataset_id="sales-2024",
        action=AccessAction.READ.value,
        purpose="Data quality check"
    ))
    print(f"   ✅ {len(lake.access_log)} access events logged\n")

    print("4️⃣  Processing GDPR deletion request...")
    lake.handle_gdpr_deletion(RequestGDPRDeletionCommand(
        lake_id=lake_id,
        subject_id="customer-42",
        reason="User requested right to be forgotten",
        requested_by="support-agent-12"
    ))
    pending = lake.get_pending_deletions()
    print(f"   ✅ Deletion request created: {pending[0]['deletion_id']}")
    print(f"   ⏰ Deadline: {pending[0]['deadline'][:10]}")
    print(f"   📝 Status: {pending[0]['status']}\n")

    print("5️⃣  Persisting events to event store...")
    events = lake.uncommitted_events
    event_store.save(lake_id, events)
    print(f"   ✅ {len(events)} events saved\n")

    print("6️⃣  Reconstructing aggregate from events...")
    loaded_events = event_store.load(lake_id)
    reconstructed = DataLakeAggregate()
    for event in loaded_events:
        reconstructed.apply(event)
    print(f"   ✅ Aggregate reconstructed from {len(loaded_events)} events")
    print(f"   📊 Datasets: {len(reconstructed.datasets)}")
    print(f"   🔍 Access logs: {len(reconstructed.access_log)}")
    print(f"   🗑️  Deletion requests: {len(reconstructed.deletion_requests)}\n")

    print("7️⃣  Creating snapshot for optimization...")
    from orchestrix.core.snapshot import Snapshot
    snapshot = Snapshot(
        aggregate_id=lake_id,
        version=len(loaded_events),
        aggregate_type="DataLakeAggregate",
        state={
            "lake_id": reconstructed.lake_id,
            "name": reconstructed.name,
            "datasets": reconstructed.datasets,
            "deletion_requests": reconstructed.deletion_requests,
            "access_log": reconstructed.access_log
        }
    )
    event_store.save_snapshot(snapshot)
    print(f"   ✅ Snapshot created at version {snapshot.version}\n")

    print("8️⃣  Compliance Report:")
    print(f"   • Lake: {lake.name}")
    print(f"   • Compliance: {lake.compliance_level.upper()}")
    print(f"   • Region: {lake.region}")
    print(f"   • Total datasets: {len(lake.datasets)}")
    print(f"   • PII datasets: {len(lake.get_pii_datasets())}")
    print(f"   • Pending deletions: {len(lake.get_pending_deletions())}")
    print(f"   • Access events: {len(lake.access_log)}")
    print(f"   • Event version: {lake.version}")

    print("\n✅ GDPR-compliant lakehouse operational!\n")


if __name__ == "__main__":
    main()
