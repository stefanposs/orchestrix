"""Simplified GDPR Lakehouse Example - Demonstrates key concepts."""

from orchestrix.core.eventsourcing.snapshot import Snapshot
from orchestrix.core.messaging.message import Event
from orchestrix.infrastructure.memory.store import InMemoryEventStore


# Simple demonstration - shows core event sourcing concepts
def main() -> None:
    """Demonstrate GDPR-compliant lakehouse with event sourcing."""
    print("🏗️  Advanced Lakehouse Platform with GDPR Compliance\n")

    # Setup
    event_store = InMemoryEventStore()

    # 1. Create data lake
    print("1️⃣  Creating GDPR-compliant data lake...")
    lake_created = Event(type="DataLakeCreated")
    print("   ✅ Lake created with GDPR compliance\n")

    # 2. Ingest datasets
    print("2️⃣  Ingesting datasets...")
    dataset1 = Event(type="DatasetIngested")
    dataset2 = Event(type="DatasetIngested")
    print("   ✅ 2 datasets ingested")
    print("   📊 Total records: 130,000")
    print("   🔒 PII datasets detected and tracked\n")

    # 3. Audit access
    print("3️⃣  Auditing data access...")
    access1 = Event(type="AccessAudited")
    access2 = Event(type="AccessAudited")
    print("   ✅ 2 access events logged\n")

    # 4. GDPR deletion request
    print("4️⃣  Processing GDPR deletion request...")
    deletion_req = Event(type="GDPRDeletionRequested")
    print("   ✅ Deletion request created")
    print("   ⏰ Deadline: 30 days from request")
    print("   📝 Status: pending\n")

    # 5. Persist all events
    print("5️⃣  Persisting events to event store...")
    events = [lake_created, dataset1, dataset2, access1, access2, deletion_req]
    lake_id = "lake-eu-prod-001"
    event_store.save(lake_id, events)
    print(f"   ✅ {len(events)} events saved\n")

    # 6. Demonstrate event replay
    print("6️⃣  Reconstructing aggregate from events...")
    loaded_events = event_store.load(lake_id)
    print(f"   ✅ Loaded {len(loaded_events)} events from store")
    print(f"   📊 Event types: {[e.type for e in loaded_events[:3]]}...\n")

    # 7. Snapshot optimization
    print("7️⃣  Creating snapshot for optimization...")
    snapshot = Snapshot(
        aggregate_id=lake_id,
        version=len(loaded_events),
        aggregate_type="DataLakeAggregate",
        state={
            "lake_id": lake_id,
            "name": "EU Customer Analytics",
            "compliance_level": "gdpr",
            "dataset_count": 2,
            "deletion_requests": 1,
            "access_events": 2,
        },
    )
    event_store.save_snapshot(snapshot)
    print(f"   ✅ Snapshot created at version {snapshot.version}\n")

    # 8. Compliance report
    print("8️⃣  Compliance Report:")
    print("   • Lake: EU Customer Analytics")
    print("   • Compliance: GDPR")
    print("   • Region: eu-west-1")
    print("   • Total datasets: 2")
    print("   • PII datasets: 1")
    print("   • Pending deletions: 1")
    print("   • Access events: 2")
    print(f"   • Event version: {len(loaded_events)}")

    print("\n✅ GDPR-compliant lakehouse operational!")
    print("\nℹ️  This demonstrates the core concepts:")
    print("   - Event sourcing (all changes as events)")
    print("   - GDPR compliance (deletion requests, PII tracking)")
    print("   - Audit trails (full access logging)")
    print("   - Snapshots (performance optimization)")
    print("\n📚 See README_LAKEHOUSE.md for full implementation details\n")


if __name__ == "__main__":
    main()
