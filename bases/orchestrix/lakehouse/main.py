"""Complete lakehouse anonymization example."""

import asyncio

from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.utils import InMemoryEventStore, InMemoryMessageBus

from .aggregate import AnonymizationJob
from .engine import AnonymizationEngine, LakehouseTable
from .handlers import register_handlers
from .models import (
    AnonymizationRule,
    AnonymizationStrategy,
    ColumnType,
    CreateAnonymizationJob,
    TableSchema,
)
from .saga import register_saga


async def run_example() -> None:
    """Run the lakehouse anonymization example."""
    print("🏢 Lakehouse Data Anonymization Example")
    print("=" * 70)
    print("GDPR Compliance: Table Anonymization with Dry-Run Validation\n")

    # Setup infrastructure
    event_store = InMemoryEventStore()
    message_bus = InMemoryMessageBus()
    repository = AggregateRepository[AnonymizationJob](event_store)
    engine = AnonymizationEngine(seed=42)

    # Create sample lakehouse table
    print("📊 Setting up sample customer table...")
    customer_table = LakehouseTable(
        database="analytics_db",
        schema_name="customer_data",
        table_name="customers",
        data=[
            {
                "customer_id": 1,
                "email": "alice.smith@company.com",
                "name": "Alice Smith",
                "phone": "+1-555-123-4567",
                "address": "123 Main St, San Francisco, CA 94105",
                "ssn": "123-45-6789",
                "date_of_birth": "1985-03-15",
                "salary": 75000.0,
                "credit_card": "4532-1234-5678-9010",
            },
            {
                "customer_id": 2,
                "email": "bob.johnson@company.com",
                "name": "Bob Johnson",
                "phone": "+1-555-234-5678",
                "address": "456 Oak Ave, New York, NY 10001",
                "ssn": "234-56-7890",
                "date_of_birth": "1990-07-22",
                "salary": 85000.0,
                "credit_card": "5412-2345-6789-0123",
            },
            {
                "customer_id": 3,
                "email": "charlie.brown@company.com",
                "name": "Charlie Brown",
                "phone": "+1-555-345-6789",
                "address": "789 Pine Rd, Chicago, IL 60601",
                "ssn": "345-67-8901",
                "date_of_birth": "1978-11-30",
                "salary": 95000.0,
                "credit_card": "6011-3456-7890-1234",
            },
            {
                "customer_id": 4,
                "email": "diana.prince@company.com",
                "name": "Diana Prince",
                "phone": "+1-555-456-7890",
                "address": "321 Elm St, Seattle, WA 98101",
                "ssn": "456-78-9012",
                "date_of_birth": "1992-05-18",
                "salary": 105000.0,
                "credit_card": "3782-4567-8901-2345",
            },
            {
                "customer_id": 5,
                "email": "eve.williams@company.com",
                "name": "Eve Williams",
                "phone": "+1-555-567-8901",
                "address": "654 Maple Dr, Austin, TX 78701",
                "ssn": "567-89-0123",
                "date_of_birth": "1988-09-25",
                "salary": 92000.0,
                "credit_card": "6011-5678-9012-3456",
            },
        ],
    )

    # Store table in simulated lakehouse
    lakehouse_tables = {"analytics_db.customer_data.customers": customer_table}

    print(f"   Database: {customer_table.database}")
    print(f"   Schema: {customer_table.schema_name}")
    print(f"   Table: {customer_table.table_name}")
    print(f"   Rows: {len(customer_table.data)}")
    print(f"   Columns: {len(customer_table.data[0])}")

    print("\n📋 Sample Data (Before Anonymization):")
    print("-" * 70)
    sample = customer_table.get_sample(3)
    for row in sample:
        print(f"   Customer {row['customer_id']}:")
        print(f"      Email: {row['email']}")
        print(f"      Name: {row['name']}")
        print(f"      Phone: {row['phone']}")
        print(f"      SSN: {row['ssn']}")
        print(f"      Salary: ${row['salary']:,.2f}")

    # Register handlers and saga
    register_handlers(message_bus, repository)
    register_saga(message_bus, repository, lakehouse_tables, engine)

    print("\n✅ Infrastructure initialized")

    # Define anonymization rules (GDPR compliance)
    print("\n📝 Defining Anonymization Rules (GDPR Compliance):")
    print("-" * 70)

    rules = [
        AnonymizationRule(
            column_name="email",
            column_type=ColumnType.EMAIL,
            strategy=AnonymizationStrategy.PSEUDONYMIZATION,
            preserve_format=True,
        ),
        AnonymizationRule(
            column_name="name",
            column_type=ColumnType.NAME,
            strategy=AnonymizationStrategy.PSEUDONYMIZATION,
        ),
        AnonymizationRule(
            column_name="phone",
            column_type=ColumnType.PHONE,
            strategy=AnonymizationStrategy.MASKING,
            preserve_format=True,
        ),
        AnonymizationRule(
            column_name="address",
            column_type=ColumnType.ADDRESS,
            strategy=AnonymizationStrategy.SUPPRESSION,
        ),
        AnonymizationRule(
            column_name="ssn",
            column_type=ColumnType.SSN,
            strategy=AnonymizationStrategy.HASHING,
        ),
        AnonymizationRule(
            column_name="salary",
            column_type=ColumnType.SALARY,
            strategy=AnonymizationStrategy.GENERALIZATION,
        ),
        AnonymizationRule(
            column_name="credit_card",
            column_type=ColumnType.CREDIT_CARD,
            strategy=AnonymizationStrategy.SUPPRESSION,
        ),
    ]

    for rule in rules:
        print(f"   • {rule.column_name:15} → {rule.strategy.value:20} ({rule.column_type.value})")

    # Create anonymization job
    print("\n🚀 Creating Anonymization Job...")
    print("-" * 70)

    table_schema = TableSchema(
        database=customer_table.database,
        schema_name=customer_table.schema_name,
        table_name=customer_table.table_name,
        columns=list(customer_table.data[0].keys()),
        row_count=len(customer_table.data),
        primary_keys=["customer_id"],
    )

    await message_bus.publish_async(
        CreateAnonymizationJob(
            job_id="anon-job-001",
            table_schema=table_schema,
            rules=rules,
            requester="data-governance-team",
            reason="GDPR Article 17: Right to erasure for customer request #CR-12345",
        )
    )

    # Wait for saga to complete (dry-run → approval → anonymization)
    print("\n⏳ Processing anonymization workflow...")
    await asyncio.sleep(1.0)

    # Show final results
    print("\n" + "=" * 70)
    print("📊 Final Results (After Anonymization):")
    print("=" * 70)

    final_sample = customer_table.get_sample(3)
    for row in final_sample:
        print(f"   Customer {row['customer_id']}:")
        print(f"      Email: {row['email']}")
        print(f"      Name: {row['name']}")
        print(f"      Phone: {row['phone']}")
        print(f"      Address: {row['address']}")
        print(f"      SSN: {row['ssn']}")
        print(f"      Salary: {row['salary']}")
        print(f"      Credit Card: {row['credit_card']}")

    # Show event history (audit trail)
    print("\n📜 Audit Trail (Event History):")
    print("=" * 70)
    events = await event_store.load_async("anon-job-001")
    for i, event in enumerate(events, 1):
        print(f"{i}. {event.type}")
        if hasattr(event, "completed_at"):
            print(f"   Completed at: {event.completed_at}")
        elif hasattr(event, "started_at"):
            print(f"   Started at: {event.started_at}")

    print("\n" + "=" * 70)
    print("✅ Anonymization Complete!")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  • Dry-run validation before anonymization")
    print("  • Multiple anonymization strategies")
    print("  • Automatic backup before changes")
    print("  • Complete audit trail (event sourcing)")
    print("  • Rollback capability on failure")
    print("  • GDPR compliance (right to erasure)")
    print("\n🎉 All data successfully anonymized!\n")


if __name__ == "__main__":
    asyncio.run(run_example())
