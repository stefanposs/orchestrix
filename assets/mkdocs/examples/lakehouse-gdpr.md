---
# Lakehouse FastAPI Demo: GDPR Compliance & Event Sourcing

Dieses Beispiel zeigt eine moderne, GDPR-konforme Lakehouse-Plattform mit Event Sourcing, FastAPI und vollständigem Audit-Trail.

**Source:**
- [Demo-Base: bases/orchestrix/lakehouse_fastapi_demo/](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/lakehouse_fastapi_demo)
- [Code: gdpr.py](https://github.com/stefanposs/orchestrix/blob/main/bases/orchestrix/lakehouse_fastapi_demo/gdpr.py)

## Features & Prozesse

- Dataset- und Contract-Registrierung
- Append-only Ingestion, Replay, Quarantine, Data Quality, Privacy, Publish, Consumption
- Event Sourcing: Jeder Schritt erzeugt Events, volle Auditierbarkeit
- GDPR-Deletion mit 30-Tage-Deadline
- Modular: Aggregates für Dataset, Contract, Batch, Lake
- FastAPI-Entrypoints für alle Kernprozesse
- Snapshots für Performance

## End-to-End API-Demo

### 1. Server starten
```bash
uv run main:start
```

### 2. Beispiel-Requests
```bash
# Dataset registrieren
curl -X POST http://localhost:8000/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "sales", "schema": {"id": "int", "amount": "float"}}'

# Contract registrieren
curl -X POST http://localhost:8000/contracts \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales", "retention_days": 365}'

# Upload-URL holen
curl -X POST http://localhost:8000/upload-url \
  -H "Content-Type: application/json" \
  -d '{"filename": "sales_2024_01.csv"}'

# Daten hochladen
echo "id,amount\n1,100.0\n2,200.0" > sales_2024_01.csv
curl -X PUT "<UPLOAD_URL>" --data-binary @sales_2024_01.csv

# Batch anhängen
curl -X POST http://localhost:8000/append-batch \
  -H "Content-Type: application/json" \
  -d '{"dataset": "sales", "contract_id": "contract1", "batch_id": "batch1", "file_url": "sales_2024_01.csv"}'

# GDPR-Deletion anstoßen
curl -X POST http://localhost:8000/run-privacy \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch1", "privacy_rules": {"id": "mask"}}'
```

---

## Architektur

```
┌──────────────┐
│   FastAPI    │  REST-API für alle Prozesse
└──────┬───────┘
       ↓
┌──────────────────┐
│ Aggregates       │  Lake, Dataset, Contract, Batch
└──────┬───────────┘
       ↓
┌──────────────┐
│    Events    │  Audit, GDPR, Ingestion, DQ, Privacy
└──────┬───────┘
       ↓
┌──────────────┐
│  Event Store │  Vollständiger Audit-Trail
└──────────────┘
       ↓
┌──────────────┐
│  Snapshots   │  Performance-Optimierung
└──────────────┘
```

## Domain Model (Auszug)

```python
class ComplianceLevel(str, Enum):
    STANDARD = "standard"
    GDPR = "gdpr"
    STRICT = "strict"

@dataclass(frozen=True)
class CreateDataLakeCommand(Command):
    lake_id: str
    name: str
    owner_id: str
    region: str
    compliance_level: str

@dataclass(frozen=True)
class IngestDatasetCommand(Command):
    lake_id: str
    dataset_id: str
    data_source: str
    record_count: int
    contains_pii: bool

@dataclass(frozen=True)
class RequestGDPRDeletionCommand(Command):
    lake_id: str
    subject_id: str
    reason: str
    requested_by: str

@dataclass(frozen=True)
class AuditAccessCommand(Command):
    lake_id: str
    accessor_id: str
    dataset_id: str
    action: str
    purpose: str
```

## Key Features

### GDPR-Deletion mit Deadline

```python
lake.handle_gdpr_deletion(RequestGDPRDeletionCommand(
    lake_id="lake-eu-prod-001",
    subject_id="customer-42",
    reason="User requested right to be forgotten",
    requested_by="support-agent-12"
))
# Deadline automatisch: 30 Tage ab Request
```

### PII-Tracking & Audit

```python
lake.handle_ingest_dataset(IngestDatasetCommand(
    lake_id="lake-eu-prod-001",
    dataset_id="sales-2024",
    data_source="salesforce_sync",
    record_count=125000,
    contains_pii=True
))

lake.handle_audit_access(AuditAccessCommand(
    lake_id="lake-eu-prod-001",
    accessor_id="analyst-456",
    dataset_id="sales-2024",
    action="query",
    purpose="Q4 revenue analysis"
))
```

### Event Sourcing & Snapshots

```python
event_store.save(lake_id, lake.uncommitted_events)
snapshot = Snapshot(
    aggregate_id=lake_id,
    version=len(events),
    aggregate_type="DataLakeAggregate",
    state={...}
)
event_store.save_snapshot(snapshot)
```

## Erweiterbarkeit & Storage

- Upload/Download über signierte URLs, Storage-Backend austauschbar (Local, S3, Azure, GCS)
- Alle Logik in bases/, keine Python-Logik in projects/
- Demo-Architektur: Einfach erweiterbar für neue Compliance- oder Storage-Anforderungen

---

**Hinweis:**
Die Demo-Base ist modular, prozessgetrieben und für Präsentation/Tests optimiert. Alle Kernprozesse sind als API und Event-Sourcing implementiert. Erweiterungen (z.B. neue Privacy-Strategien, Storage-Backends) sind mit minimalem Aufwand möglich.

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

- **Data Anonymization** - Anonymize PII in datasets (see `bases/orchestrix/lakehouse/main.py`)
- **E-Commerce** - Order processing with sagas (see `bases/orchestrix/ecommerce/`)
- **Banking** - Account management basics (see `bases/orchestrix/banking/`)

## Learn More

- [Event Sourcing Guide](../guide/event-store.md)
- [Aggregate Pattern](../guide/best-practices.md#aggregates)
- [Testing Strategies](../development/testing.md)

## Source Code

Explore the complete implementation on GitHub:

- [`gdpr_simple.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/lakehouse/gdpr_simple.py) - Simple runnable demo (90 lines)
- [`gdpr.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/lakehouse/gdpr.py) - Full implementation with aggregates (400 lines)
- [`models.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/lakehouse/models.py) - Domain model (Commands, Events, Enums)
- [`aggregate.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/lakehouse/aggregate.py) - Business logic and state management
- [`example.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/lakehouse/example.py) - Data anonymization example

**Complete Lakehouse Examples:** [Browse on GitHub](https://github.com/stefanposs/orchestrix/tree/main/examples/lakehouse)
