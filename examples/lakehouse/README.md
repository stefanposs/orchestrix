"""Lakehouse Data Anonymization Example

This example demonstrates a production-ready workflow for anonymizing sensitive data
in a lakehouse platform with GDPR compliance.

## Workflow

```
1. Create Anonymization Job
   ↓
2. Automatic Dry-Run Validation
   • Test anonymization on copy
   • Show before/after samples
   • Estimate duration
   • Identify warnings
   ↓
3. Manual Approval (or auto-approve)
   ↓
4. Automatic Backup Creation
   ↓
5. Execute Anonymization
   • Apply rules column by column
   • Track progress via events
   • Audit trail for compliance
   ↓
6. Success → Completed
   OR
   Failure → Automatic Rollback
```

## Anonymization Strategies

### 1. **Masking**
Replace characters with asterisks while optionally preserving format.

**Example:**
```
Email: alice@company.com → a***@c******.com
Phone: +1-555-123-4567 → +1-***-***-****
```

**Use cases:** Partial data visibility, testing environments

### 2. **Hashing**
Generate SHA-256 hash for consistent anonymization.

**Example:**
```
SSN: 123-45-6789 → e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Use cases:** Unique identifiers, referential integrity

### 3. **Tokenization**
Replace with random alphanumeric token.

**Example:**
```
Account: ACC-12345 → TKN-XY9K2
```

**Use cases:** One-time use, no reversibility needed

### 4. **Generalization**
Reduce precision to broader categories.

**Example:**
```
Age: 34 → "30-39"
Salary: $75,000 → "50k-75k"
Zipcode: 94105 → "941**"
Date: 1985-03-15 → "1985"
```

**Use cases:** Analytics, aggregated reporting

### 5. **Suppression**
Delete data entirely (set to NULL).

**Example:**
```
Address: "123 Main St" → NULL
Credit Card: "4532-***" → NULL
```

**Use cases:** GDPR right to erasure, unnecessary PII

### 6. **Pseudonymization**
Replace with consistent fake data using hash-based seeding.

**Example:**
```
Name: "Alice Smith" → "Jane Johnson"
Email: "alice@company.com" → "jane123@example.com"
Phone: "+1-555-123-4567" → "+1-555-789-0123"
```

**Use cases:** Realistic test data, development environments

### 7. **Noise**
Add random noise to numeric values.

**Example:**
```
Salary: $75,000 → $74,123 (±10% noise)
Age: 34 → 35
```

**Use cases:** Statistical analysis, differential privacy

### 8. **Aggregation**
Group values into buckets.

**Example:**
```
[100, 110, 105, 95] → "~103"
```

**Use cases:** Privacy-preserving analytics

## Usage

```python
import asyncio
from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus
from examples.lakehouse.models import (
    AnonymizationRule,
    AnonymizationStrategy,
    ColumnType,
    CreateAnonymizationJob,
    TableSchema,
)
from examples.lakehouse.engine import AnonymizationEngine, LakehouseTable
from examples.lakehouse.handlers import register_handlers
from examples.lakehouse.saga import register_saga


async def anonymize_customer_data():
    # Setup
    event_store = InMemoryEventStore()
    message_bus = InMemoryMessageBus()
    repository = AggregateRepository(event_store)
    engine = AnonymizationEngine()

    # Create table
    customer_table = LakehouseTable(
        database="analytics",
        schema_name="customer_data",
        table_name="customers",
        data=[
            {"id": 1, "email": "alice@company.com", "ssn": "123-45-6789"},
            {"id": 2, "email": "bob@company.com", "ssn": "234-56-7890"},
        ],
    )

    lakehouse_tables = {"analytics.customer_data.customers": customer_table}

    # Register handlers
    register_handlers(message_bus, repository)
    register_saga(message_bus, repository, lakehouse_tables, engine)

    # Define rules
    rules = [
        AnonymizationRule(
            column_name="email",
            column_type=ColumnType.EMAIL,
            strategy=AnonymizationStrategy.PSEUDONYMIZATION,
        ),
        AnonymizationRule(
            column_name="ssn",
            column_type=ColumnType.SSN,
            strategy=AnonymizationStrategy.HASHING,
        ),
    ]

    # Create job (saga automatically runs dry-run → approval → anonymization)
    await message_bus.publish_async(
        CreateAnonymizationJob(
            job_id="job-001",
            table_schema=TableSchema(
                database="analytics",
                schema_name="customer_data",
                table_name="customers",
                columns=["id", "email", "ssn"],
                row_count=2,
                primary_keys=["id"],
            ),
            rules=rules,
            requester="data-governance",
            reason="GDPR Article 17: Right to erasure",
        )
    )

    await asyncio.sleep(1)  # Wait for saga completion


if __name__ == "__main__":
    asyncio.run(anonymize_customer_data())
```

## GDPR Compliance

### Article 17: Right to Erasure
```python
# Customer requests data deletion
rules = [
    AnonymizationRule("email", ColumnType.EMAIL, AnonymizationStrategy.SUPPRESSION),
    AnonymizationRule("name", ColumnType.NAME, AnonymizationStrategy.SUPPRESSION),
    AnonymizationRule("phone", ColumnType.PHONE, AnonymizationStrategy.SUPPRESSION),
    AnonymizationRule("address", ColumnType.ADDRESS, AnonymizationStrategy.SUPPRESSION),
]
```

### Article 5: Data Minimization
```python
# Remove unnecessary PII for analytics
rules = [
    AnonymizationRule("name", ColumnType.NAME, AnonymizationStrategy.PSEUDONYMIZATION),
    AnonymizationRule("age", ColumnType.GENERIC_PII, AnonymizationStrategy.GENERALIZATION),
    AnonymizationRule("salary", ColumnType.SALARY, AnonymizationStrategy.GENERALIZATION),
]
```

### Article 32: Pseudonymization
```python
# Pseudonymize for testing environment
rules = [
    AnonymizationRule("email", ColumnType.EMAIL, AnonymizationStrategy.PSEUDONYMIZATION, preserve_format=True),
    AnonymizationRule("phone", ColumnType.PHONE, AnonymizationStrategy.PSEUDONYMIZATION),
    AnonymizationRule("name", ColumnType.NAME, AnonymizationStrategy.PSEUDONYMIZATION),
]
```

## Key Features

### 1. Dry-Run Validation
Test anonymization before applying:
```python
# Saga automatically runs dry-run
# Shows before/after samples
# Estimates duration
# Identifies potential issues
```

**Dry-run output:**
```
🧪 Dry-run started
   - Testing email: pseudonymization
   - Testing name: pseudonymization
   - Testing phone: masking
✅ Dry-run completed
   Affected rows: 5
   Affected columns: email, name, phone
   Sample Preview:
   email:
      Before: ['alice@company.com', 'bob@company.com']
      After:  ['john123@example.com', 'jane456@test.org']
```

### 2. Automatic Backup
Before anonymization, create backup:
```python
# Saga creates backup automatically
backup_location = "s3://backups/analytics/customer_data/customers/backup.parquet"
```

### 3. Rollback Capability
If anonymization fails, automatic rollback:
```python
try:
    anonymize_column(...)
except Exception as e:
    # Saga automatically triggers rollback
    restore_from_backup()
```

### 4. Audit Trail
Complete event history for compliance:
```
1. AnonymizationJobCreated
2. DryRunStarted
3. DryRunCompleted
4. ValidationPassed
5. AnonymizationStarted
6. ColumnAnonymized (email)
7. ColumnAnonymized (name)
8. ColumnAnonymized (phone)
9. AnonymizationCompleted
```

### 5. Progress Tracking
Monitor anonymization progress:
```python
# Each column emits ColumnAnonymized event
events = await event_store.load_async(job_id)
progress = len([e for e in events if e.type == "ColumnAnonymized"])
total_columns = len(rules)
percentage = (progress / total_columns) * 100
```

## Production Integration

### Integration with Delta Lake
```python
from delta import DeltaTable

# Read Delta table
delta_table = DeltaTable.forPath(spark, "s3://lakehouse/customer_data/customers")
df = delta_table.toDF()

# Convert to LakehouseTable
lakehouse_table = LakehouseTable(
    database="analytics",
    schema_name="customer_data",
    table_name="customers",
    data=df.toPandas().to_dict('records'),
)

# Anonymize
await anonymize(lakehouse_table, rules)

# Write back
spark.createDataFrame(lakehouse_table.data).write.format("delta").mode("overwrite").save(...)
```

### Integration with Apache Iceberg
```python
from pyiceberg.catalog import load_catalog

# Load Iceberg table
catalog = load_catalog("default")
table = catalog.load_table("analytics.customer_data.customers")
df = table.scan().to_pandas()

# Anonymize
lakehouse_table = LakehouseTable(..., data=df.to_dict('records'))
await anonymize(lakehouse_table, rules)

# Append or overwrite
table.append(lakehouse_table.data)
```

### Integration with Databricks
```python
# Read from Databricks table
df = spark.table("analytics.customer_data.customers")

# Anonymize
lakehouse_table = LakehouseTable(..., data=df.toPandas().to_dict('records'))
await anonymize(lakehouse_table, rules)

# Write back
spark.createDataFrame(lakehouse_table.data).write.mode("overwrite").saveAsTable(...)
```

## Advanced Scenarios

### Conditional Anonymization
Only anonymize rows matching criteria:
```python
# Only anonymize churned customers
rules = [
    AnonymizationRule("email", ColumnType.EMAIL, AnonymizationStrategy.SUPPRESSION),
]

# Filter in preprocessing
customer_table.data = [
    row for row in customer_table.data if row.get("status") == "churned"
]
```

### Partial Column Anonymization
Different strategies for different segments:
```python
# VIP customers: pseudonymize (keep for analytics)
# Regular customers: suppress (full deletion)

for row in customer_table.data:
    if row["tier"] == "VIP":
        row["email"] = engine.pseudonymization(row["email"], "email")
    else:
        row["email"] = None
```

### Cross-Table Referential Integrity
Maintain relationships across tables:
```python
# Use hashing to preserve relationships
rules_customers = [
    AnonymizationRule("customer_id", ColumnType.GENERIC_PII, AnonymizationStrategy.HASHING),
]

rules_orders = [
    AnonymizationRule("customer_id", ColumnType.GENERIC_PII, AnonymizationStrategy.HASHING),
]

# Same hash ensures FK relationships preserved
```

### Time-Based Expiration
Auto-anonymize old data:
```python
from datetime import datetime, timedelta

# Anonymize data older than 7 years (GDPR requirement)
cutoff_date = datetime.now() - timedelta(days=7*365)

customer_table.data = [
    row for row in customer_table.data
    if datetime.fromisoformat(row["created_at"]) < cutoff_date
]
```

## Monitoring & Alerts

### Track Anonymization Metrics
```python
# Subscribe to events
def track_metrics(event):
    if event.type == "AnonymizationCompleted":
        metrics.increment("anonymization.completed")
        metrics.gauge("anonymization.rows", event.data.total_rows_affected)
        metrics.timer("anonymization.duration", event.data.duration_seconds)
    elif event.type == "AnonymizationFailed":
        metrics.increment("anonymization.failed")
        alert("Anonymization failed: " + event.data.reason)

message_bus.subscribe(AnonymizationCompleted, track_metrics)
message_bus.subscribe(AnonymizationFailed, track_metrics)
```

### SLA Monitoring
```python
# Alert if anonymization takes too long
if dry_run_result.estimated_duration_seconds > 3600:  # 1 hour
    alert(f"Large anonymization job: {estimated_duration_seconds}s")
```

## Testing

```python
async def test_anonymization_preserves_null():
    table = LakehouseTable(
        database="test",
        schema_name="test",
        table_name="test",
        data=[
            {"id": 1, "email": "alice@example.com"},
            {"id": 2, "email": None},  # NULL value
        ],
    )

    rule = AnonymizationRule(
        column_name="email",
        column_type=ColumnType.EMAIL,
        strategy=AnonymizationStrategy.MASKING,
        preserve_null=True,
    )

    engine = AnonymizationEngine()
    table.anonymize_column("email", engine, "masking", preserve_null=True)

    # NULL values should remain NULL
    assert table.data[0]["email"] != "alice@example.com"
    assert table.data[1]["email"] is None


async def test_dry_run_shows_warnings():
    # Test dry-run with invalid column
    rules = [
        AnonymizationRule(
            column_name="non_existent_column",
            column_type=ColumnType.EMAIL,
            strategy=AnonymizationStrategy.MASKING,
        )
    ]

    # Dry-run should show warning
    result = await execute_dry_run(table, rules)
    assert "not found" in result.warnings[0]
```

## Security Considerations

1. **Access Control**: Restrict anonymization job creation to authorized users
2. **Audit Logging**: All operations logged via event sourcing
3. **Backup Encryption**: Encrypt backups at rest
4. **Irreversibility**: Hashing and suppression cannot be reversed
5. **Key Management**: Secure storage of pseudonymization seeds

## Performance Optimization

1. **Batch Processing**: Process multiple columns in parallel
2. **Incremental Anonymization**: Only process changed rows
3. **Partitioned Processing**: Split large tables into partitions
4. **Caching**: Cache anonymization engine for reuse
5. **Async Execution**: Use asyncio for concurrent column processing

---

**This example demonstrates production-ready data anonymization with GDPR compliance, 
comprehensive audit trails, and robust error handling.**
"""
