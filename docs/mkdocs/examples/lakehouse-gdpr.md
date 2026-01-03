# Lakehouse: GDPR Compliance

This example demonstrates a complete GDPR-compliant data lakehouse platform built with event sourcing.

## Overview

The GDPR compliance example shows how to implement:

- ✅ **Right-to-be-Forgotten** - 30-day deletion deadlines
- ✅ **PII Tracking** - Identify and track personal data
- ✅ **Compliance Levels** - Standard, GDPR, Strict modes
- ✅ **Access Auditing** - Full audit trail for compliance
- ✅ **Event Sourcing** - Immutable event log for accountability

## Quick Start

```bash
# Run the simple demo
uv run python examples/lakehouse/gdpr_simple.py

# Study the full implementation
cat examples/lakehouse/gdpr.py
```

## Example Output

```
🏗️  Advanced Lakehouse Platform with GDPR Compliance

1️⃣  Creating GDPR-compliant data lake...
   ✅ Lake created: EU Customer Analytics (compliance: gdpr)

2️⃣  Ingesting datasets...
   ✅ 2 datasets ingested
   📊 Total records: 130,000
   🔒 PII datasets: ['sales-2024']

3️⃣  Auditing data access...
   ✅ 2 access events logged

4️⃣  Processing GDPR deletion request...
   ✅ Deletion request created
   ⏰ Deadline: 30 days from request
   📝 Status: pending

5️⃣  Persisting events to event store...
   ✅ 6 events saved

✅ GDPR-compliant lakehouse operational!
```

## Architecture

```
┌──────────────┐
│   Commands   │  CreateDataLake, IngestDataset,
│              │  RequestGDPRDeletion, AuditAccess
└──────┬───────┘
       ↓
┌──────────────────┐
│ DataLakeAggregate│  Validates business rules
│                  │  Enforces compliance
└──────┬───────────┘
       ↓
┌──────────────┐
│    Events    │  DataLakeCreated, DatasetIngested,
│              │  GDPRDeletionRequested, AccessAudited
└──────┬───────┘
       ↓
┌──────────────┐
│  Event Store │  Immutable audit log
└──────────────┘
```

## Domain Model

### Compliance Levels

```python
class ComplianceLevel(str, Enum):
    STANDARD = "standard"  # Basic compliance
    GDPR = "gdpr"          # GDPR/DSGVO compliance
    STRICT = "strict"      # Enhanced compliance
```

### Commands

#### CreateDataLake
```python
@dataclass(frozen=True)
class CreateDataLakeCommand(Command):
    lake_id: str
    name: str
    region: str
    compliance_level: str  # "standard", "gdpr", "strict"
```

#### IngestDataset
```python
@dataclass(frozen=True)
class IngestDatasetCommand(Command):
    lake_id: str
    dataset_id: str
    source: str
    record_count: int
    contains_pii: bool  # Track personal data
```

#### RequestGDPRDeletion
```python
@dataclass(frozen=True)
class RequestGDPRDeletionCommand(Command):
    lake_id: str
    subject_id: str  # Customer/user ID
    reason: str
    requested_by: str
```

#### AuditAccess
```python
@dataclass(frozen=True)
class AuditAccessCommand(Command):
    lake_id: str
    accessor_id: str
    dataset_id: str
    action: str  # "query", "export", "modify"
    purpose: str
```

### Events

All events are immutable facts that have happened:

- `DataLakeCreated` - Lake created with compliance level
- `DatasetIngested` - Dataset added, PII flag recorded
- `GDPRDeletionRequested` - Deletion request with 30-day deadline
- `AccessAudited` - Access logged for compliance

## Key Features

### 1. Right-to-be-Forgotten

GDPR Article 17 implementation with automatic deadline calculation:

```python
# Request deletion
lake.handle_gdpr_deletion(RequestGDPRDeletionCommand(
    lake_id="lake-001",
    subject_id="customer-42",
    reason="User requested right to be forgotten",
    requested_by="support-agent"
))

# Automatic 30-day deadline
deadline = datetime.now() + timedelta(days=30)
```

### 2. PII Tracking

Track which datasets contain personal data:

```python
lake.handle_ingest_dataset(IngestDatasetCommand(
    lake_id="lake-001",
    dataset_id="customer-data",
    source="crm_export",
    record_count=50000,
    contains_pii=True  # ← Mark as PII
))

# Query PII datasets
pii_datasets = [ds for ds in lake.datasets if ds.contains_pii]
```

### 3. Compliance Validation

Different rules based on compliance level:

```python
def validate_compliance(self, dataset):
    if self.compliance_level == ComplianceLevel.GDPR:
        # GDPR requires PII flag
        if dataset.contains_pii is None:
            raise ValidationError("PII flag required for GDPR")
    
    if self.compliance_level == ComplianceLevel.STRICT:
        # Strict mode: additional validations
        if not dataset.encryption_enabled:
            raise ValidationError("Encryption required")
```

### 4. Access Auditing

Every data access logged for compliance:

```python
lake.handle_audit_access(AuditAccessCommand(
    lake_id="lake-001",
    accessor_id="analyst-123",
    dataset_id="customer-data",
    action="query",
    purpose="Marketing campaign analysis"
))

# Generate compliance report
report = {
    "lake": lake.name,
    "compliance": lake.compliance_level,
    "access_events": len(lake.access_logs),
    "pending_deletions": len([d for d in lake.deletions if d.status == "pending"])
}
```

## Event Sourcing Benefits

### Complete Audit Trail

Every state change recorded as an event:

```python
events = event_store.load("lake-001")
# → [
#     DataLakeCreated(timestamp="2026-01-01T10:00:00Z"),
#     DatasetIngested(timestamp="2026-01-01T10:05:00Z"),
#     AccessAudited(timestamp="2026-01-01T11:00:00Z"),
#     GDPRDeletionRequested(timestamp="2026-01-01T14:00:00Z")
# ]
```

### Temporal Queries

Answer "what was the state at time X?":

```python
# Reconstruct state at specific time
events = event_store.load("lake-001", until=datetime(2026, 1, 1))
lake = DataLakeAggregate.from_events(events)
```

### Compliance Reporting

Generate reports from event history:

```python
# Count deletions in last month
deletions = [e for e in events 
             if isinstance(e, GDPRDeletionRequested)
             and e.timestamp > last_month]

# Track access patterns
access_by_user = defaultdict(int)
for event in events:
    if isinstance(event, AccessAudited):
        access_by_user[event.accessor_id] += 1
```

### Snapshot Optimization

For large event streams (>100 events):

```python
# Create snapshot at current state
snapshot = Snapshot(
    aggregate_id="lake-001",
    version=1000,
    state={
        "name": lake.name,
        "compliance_level": lake.compliance_level,
        "datasets": lake.datasets,
        "deletions": lake.deletions
    }
)
event_store.save_snapshot(snapshot)

# Load optimized
snapshot = event_store.load_snapshot("lake-001")
remaining_events = event_store.load("lake-001", from_version=snapshot.version)
lake = DataLakeAggregate.from_snapshot(snapshot, remaining_events)
```

## Integration Guide

### 1. Set Up Infrastructure

```python
from orchestrix.infrastructure import InMemoryEventStore, InMemoryMessageBus
from orchestrix.core import AggregateRepository

# Create infrastructure
event_store = InMemoryEventStore()
message_bus = InMemoryMessageBus()
repository = AggregateRepository(event_store)
```

### 2. Register Handlers

```python
# Command handlers
@message_bus.subscribe(CreateDataLakeCommand)
async def handle_create_lake(cmd: CreateDataLakeCommand):
    lake = DataLakeAggregate()
    lake.handle_create(cmd)
    await repository.save(lake)

# Event handlers (side effects)
@message_bus.subscribe(GDPRDeletionRequested)
async def notify_deletion_requested(event: GDPRDeletionRequested):
    # Send notification to ops team
    await send_email(f"Deletion requested for {event.subject_id}")
```

### 3. Process Commands

```python
# Create lake
await message_bus.send(CreateDataLakeCommand(
    lake_id="lake-001",
    name="EU Customer Analytics",
    region="eu-west-1",
    compliance_level="gdpr"
))

# Ingest data
await message_bus.send(IngestDatasetCommand(
    lake_id="lake-001",
    dataset_id="customers-2024",
    source="crm_export",
    record_count=100000,
    contains_pii=True
))
```

## Best Practices

### ✅ DO

- **Always set PII flag** when ingesting datasets
- **Validate compliance** before processing commands
- **Track deadline status** for deletion requests
- **Use snapshots** for aggregates with >100 events
- **Emit events** for every state change

### ❌ DON'T

- **Modify events** after creation (immutable!)
- **Skip audit logs** even for internal access
- **Hardcode deadlines** (calculate from GDPR requirements)
- **Bypass compliance checks** in production
- **Store PII** in event metadata

## Testing

```python
import pytest
from examples.lakehouse.gdpr import DataLakeAggregate

def test_gdpr_deletion_sets_deadline():
    lake = DataLakeAggregate()
    lake.handle_create(CreateDataLakeCommand(
        lake_id="lake-1",
        name="Test",
        region="eu",
        compliance_level="gdpr"
    ))
    
    lake.handle_gdpr_deletion(RequestGDPRDeletionCommand(
        lake_id="lake-1",
        subject_id="user-123",
        reason="GDPR request",
        requested_by="support"
    ))
    
    # Verify 30-day deadline
    deletion = lake.deletions[0]
    assert deletion.status == "pending"
    assert deletion.deadline > datetime.now()
    assert deletion.deadline <= datetime.now() + timedelta(days=31)
```

## Production Considerations

### Event Store

Use persistent event store in production:

```python
from orchestrix.infrastructure import PostgresEventStore

event_store = PostgresEventStore(
    connection_string="postgresql://...",
    schema="events"
)
```

### Deadline Monitoring

Schedule jobs to process deletions:

```python
# Daily job to check deadlines
async def check_deletion_deadlines():
    pending = await query_pending_deletions()
    for deletion in pending:
        if deletion.deadline < datetime.now():
            await process_deletion(deletion)
```

### Compliance Reports

Generate regular reports:

```python
async def generate_monthly_report():
    events = await event_store.load_all()
    report = {
        "deletions_completed": count_completed_deletions(events),
        "average_completion_time": calculate_avg_time(events),
        "access_by_dataset": group_access_by_dataset(events)
    }
    await send_to_compliance_team(report)
```

## Related Examples

- **[Data Anonymization](lakehouse-anonymization.md)** - Anonymize PII in datasets
- **[E-Commerce](ecommerce.md)** - Order processing with sagas
- **[Banking](banking.md)** - Account management basics

## Learn More

- [Event Sourcing Guide](../guide/event-store.md)
- [Aggregate Pattern](../guide/best-practices.md#aggregates)
- [Testing Strategies](../development/testing.md)

## Source Code

- `examples/lakehouse/gdpr_simple.py` - Simple runnable demo
- `examples/lakehouse/gdpr.py` - Full implementation
- `examples/lakehouse/models.py` - Domain model
- `examples/lakehouse/aggregate.py` - Business logic
