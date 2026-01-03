# Advanced Lakehouse Platform - GDPR Compliance Example

Dieses Beispiel demonstriert eine vollständige Event-Sourcing-basierte Data Lakehouse Platform mit GDPR-Compliance.

## Features

✅ **GDPR-Compliance**
- Compliance-Level Management (Standard, GDPR, Strict)
- Right-to-be-forgotten Implementation
- 30-Tage-Löschfristen nach DSGVO
- Vollständige Audit-Trails

✅ **Event Sourcing**
- Vollständige Event-Historie aller Änderungen
- Event Replay für Aggregate-Rekonstruktion  
- Snapshot-Optimierung bei großen Event-Streams
- Immutable Event-Log

✅ **Data Lake Management**
- Dataset-Ingestion mit PII-Tracking
- Compliance-Level-basierte Validierung
- Access Auditing für Compliance-Reports
- Multi-Region Support

## Architektur

```
Command → Aggregate → Event → Event Store
                ↓
           State Update
                ↓
         Query Functions
```

### Domain Model

**Commands:**
- `CreateDataLakeCommand` - Erstellt einen neuen Data Lake
- `IngestDatasetCommand` - Ingesti ein Dataset  
- `RequestGDPRDeletionCommand` - DSGVO Löschanfrage
- `AuditAccessCommand` - Audit-Logging

**Events:**
- `DataLakeCreatedEvent` - Lake wurde erstellt
- `DatasetIngestedEvent` - Dataset wurde hinzugefügt
- `GDPRDeletionRequestedEvent` - Löschung wurde angefordert
- `AccessAuditedEvent` - Zugriff wurde geloggt

**Aggregate:**
- `DataLakeAggregate` - Verwaltet kompletten Lake-Lifecycle

## Ausführung

```bash
# Basis-Demo
uv run python examples/lakehouse_gdpr_simple.py

# Tests (wenn vorhanden)
uv run pytest examples/test_lakehouse.py -v
```

## Output

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
   ✅ Deletion request created: del-customer-42-1234567890
   ⏰ Deadline: 2026-02-02
   📝 Status: pending

5️⃣  Persisting events to event store...
   ✅ 5 events saved

6️⃣  Reconstructing aggregate from events...
   ✅ Aggregate reconstructed from 5 events
   📊 Datasets: 2
   🔍 Access logs: 2
   🗑️  Deletion requests: 1

7️⃣  Creating snapshot for optimization...
   ✅ Snapshot created at version 5

8️⃣  Compliance Report:
   • Lake: EU Customer Analytics
   • Compliance: GDPR
   • Region: eu-west-1
   • Total datasets: 2
   • PII datasets: 1
   • Pending deletions: 1
   • Access events: 2
   • Event version: 5

✅ GDPR-compliant lakehouse operational!
```

## GDPR-Compliance Features

### 1. Compliance Levels

```python
class ComplianceLevel(str, Enum):
    STANDARD = "standard"  # Basis-Compliance
    GDPR = "gdpr"          # DSGVO-Compliance
    STRICT = "strict"      # Erweiterte Compliance
```

### 2. Right-to-be-Forgotten

```python
lake.handle_gdpr_deletion(RequestGDPRDeletionCommand(
    lake_id="lake-001",
    subject_id="customer-42",
    reason="User requested right to be forgotten",
    requested_by="support-agent"
))
```

- Automatische 30-Tage-Deadline
- Status-Tracking (pending → completed)
- Vollständiger Audit-Trail

### 3. PII-Tracking

```python
lake.handle_ingest_dataset(IngestDatasetCommand(
    lake_id="lake-001",
    dataset_id="customer-data",
    source="crm_export",
    record_count=50000,
    contains_pii=True  # ← PII Flag
))
```

### 4. Access Auditing

```python
lake.handle_audit_access(AuditAccessCommand(
    lake_id="lake-001",
    accessor_id="analyst-123",
    dataset_id="customer-data",
    action=AccessAction.QUERY.value,
    purpose="Marketing analysis"
))
```

## Event Sourcing Benefits

### 1. Vollständige Historie

Alle Änderungen werden als Events gespeichert:
```python
events = event_store.load("lake-001")
# → [DataLakeCreated, DatasetIngested, AccessAudited, ...]
```

### 2. Audit-Trail

DSGVO-konforme Nachverfolgung aller Aktionen:
```python
# Wer hat wann was gemacht?
for event in events:
    print(f"{event.timestamp}: {event.type}")
```

### 3. Snapshot-Optimierung

Bei großen Event-Streams:
```python
snapshot = Snapshot(
    aggregate_id="lake-001",
    version=1000,
    state=lake.to_dict()
)
event_store.save_snapshot(snapshot)

# Laden optimiert:
snapshot = event_store.load_snapshot("lake-001")
remaining = event_store.load("lake-001", from_version=snapshot.version)
```

## Integration in eigene Projekte

### 1. Eigene Commands definieren

```python
class YourCommand(Command):
    def __init__(self, param1: str, param2: int, **kwargs):
        super().__init__(**kwargs)
        # NICHT mit self.param = param, da frozen!
```

### 2. Eigene Events definieren

```python
class YourEvent(Event):
    def __init__(self, data: str, **kwargs):
        super().__init__(**kwargs)
        # Speichere als Attribute
```

### 3. Eigenes Aggregate erstellen

```python
from orchestrix.core.aggregate import AggregateRoot

class YourAggregate(AggregateRoot):
    def handle_command(self, cmd):
        event = YourEvent(data=cmd.data)
        self._apply_event(event)  # ← _apply_event nutzen!
    
    def _when_your_event(self, event: YourEvent):  # ← _when_ prefix!
        # State-Update hier
        pass
```

## Best Practices

1. **Immutable Events** - Events niemals ändern
2. **Event Naming** - Vergangene Zeit (Created, Updated, Deleted)
3. **State in Aggregate** - Nur im Aggregate, nie in Events
4. **Validation** - Vor Event-Erstellung validieren
5. **Snapshots** - Bei > 100 Events pro Aggregate

## Weitere Beispiele

- `/examples/notifications.py` - Retry-Logic mit Dead Letter Queue
- `/examples/lakehouse_anonymization.py` - Data Anonymization
- `/tests/` - Umfangreiche Test-Suites

## Lizenz

Siehe LICENSE file.
