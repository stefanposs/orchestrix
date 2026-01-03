"""Example: Event versioning and schema evolution.

This example demonstrates how to handle event schema evolution in production
using upcasters. As domain models change, events must migrate to new schemas
while maintaining compatibility with events stored in old formats.

Scenario:
- Original OrderCreated event (v1) with basic fields
- Later, we add currency support (v2)
- Then we add creator metadata (v3)
- Old events are automatically upgraded as they're loaded
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from orchestrix.core.message import Event
from orchestrix.core.versioning import EventUpcaster, UpcasterRegistry


# Event versions showing schema evolution
@dataclass(frozen=True)
class OrderCreatedV1(Event):
    """Original order creation schema - minimal fields."""

    order_id: str
    customer_id: str
    total: float
    version: int = 1


@dataclass(frozen=True)
class OrderCreatedV2(Event):
    """Version 2: Added currency field to support multi-currency."""

    order_id: str
    customer_id: str
    total: float
    currency: str
    version: int = 2


@dataclass(frozen=True)
class OrderCreatedV3(Event):
    """Version 3: Added creator metadata for audit trail."""

    order_id: str
    customer_id: str
    total: float
    currency: str
    created_by: str
    version: int = 3


# Upcasters implementing the migration logic
class OrderCreatedV1toV2(EventUpcaster[OrderCreatedV1, OrderCreatedV2]):
    """Migrate OrderCreated from v1 to v2 by adding currency.

    Legacy events are assumed to be in USD (common default).
    """

    def __init__(self) -> None:
        super().__init__(source_version=1, target_version=2)

    async def upcast(self, event: OrderCreatedV1) -> OrderCreatedV2:
        print(f"  → Upgrading v1→v2: {event.order_id} (USD default)")
        return OrderCreatedV2(
            order_id=event.order_id,
            customer_id=event.customer_id,
            total=event.total,
            currency="USD",  # Default for legacy events
        )


class OrderCreatedV2toV3(EventUpcaster[OrderCreatedV2, OrderCreatedV3]):
    """Migrate OrderCreated from v2 to v3 by adding creator metadata.

    Legacy events are attributed to the system.
    """

    def __init__(self) -> None:
        super().__init__(source_version=2, target_version=3)

    async def upcast(self, event: OrderCreatedV2) -> OrderCreatedV3:
        print(f"  → Upgrading v2→v3: {event.order_id} (system creator)")
        return OrderCreatedV3(
            order_id=event.order_id,
            customer_id=event.customer_id,
            total=event.total,
            currency=event.currency,
            created_by="system",  # Default for legacy events
        )


async def main() -> None:
    """Demonstrate event versioning and automatic upcasting."""

    print("=" * 70)
    print("EVENT VERSIONING & SCHEMA EVOLUTION EXAMPLE")
    print("=" * 70)

    # Setup registry
    registry = UpcasterRegistry()
    registry.register("OrderCreated", OrderCreatedV1toV2())
    registry.register("OrderCreated", OrderCreatedV2toV3())

    print("\n📋 Upcasting paths registered:")
    for source, target in registry.get_chain_info("OrderCreated"):
        print(f"  • v{source} → v{target}")

    # Scenario 1: Upcast single-step
    print("\n" + "=" * 70)
    print("SCENARIO 1: Single-step upcasting (v1→v2)")
    print("=" * 70)

    event_v1 = OrderCreatedV1(
        order_id="ORD-001", customer_id="CUST-123", total=99.99
    )
    print(f"\n🔴 Original event (v1):")
    print(f"  • order_id: {event_v1.order_id}")
    print(f"  • customer_id: {event_v1.customer_id}")
    print(f"  • total: {event_v1.total}")

    event_v2 = await registry.upcast(event_v1, "OrderCreated", target_version=2)
    print(f"\n🟢 After upcasting to v2:")
    print(f"  • order_id: {event_v2.order_id}")
    print(f"  • customer_id: {event_v2.customer_id}")
    print(f"  • total: {event_v2.total}")
    print(f"  • currency: {event_v2.currency} (NEW)")

    # Scenario 2: Upcast multi-step chain
    print("\n" + "=" * 70)
    print("SCENARIO 2: Multi-step upcasting (v1→v2→v3)")
    print("=" * 70)

    event_v1_new = OrderCreatedV1(
        order_id="ORD-002", customer_id="CUST-456", total=149.50
    )
    print(f"\n🔴 Original event (v1):")
    print(f"  • order_id: {event_v1_new.order_id}")
    print(f"  • customer_id: {event_v1_new.customer_id}")
    print(f"  • total: {event_v1_new.total}")

    event_v3 = await registry.upcast(
        event_v1_new, "OrderCreated", target_version=3
    )
    print(f"\n🟢 After upcasting to v3:")
    print(f"  • order_id: {event_v3.order_id}")
    print(f"  • customer_id: {event_v3.customer_id}")
    print(f"  • total: {event_v3.total}")
    print(f"  • currency: {event_v3.currency} (v2 addition)")
    print(f"  • created_by: {event_v3.created_by} (v3 addition)")

    # Scenario 3: Skip intermediate version
    print("\n" + "=" * 70)
    print("SCENARIO 3: Upcast to intermediate version (v1→v2, skip v3)")
    print("=" * 70)

    event_v1_third = OrderCreatedV1(
        order_id="ORD-003", customer_id="CUST-789", total=249.99
    )
    print(f"\n🔴 Original event (v1):")
    print(f"  • order_id: {event_v1_third.order_id}")

    event_v2_only = await registry.upcast(
        event_v1_third, "OrderCreated", target_version=2
    )
    print(f"\n🟢 After upcasting to v2 (not v3):")
    print(f"  • order_id: {event_v2_only.order_id}")
    print(f"  • currency: {event_v2_only.currency}")
    print(f"  • created_by: {getattr(event_v2_only, 'created_by', 'NOT SET')} (not added)")

    # Scenario 4: No-op when already at target version
    print("\n" + "=" * 70)
    print("SCENARIO 4: Event already at target version (no change)")
    print("=" * 70)

    event_v3_existing = OrderCreatedV3(
        order_id="ORD-004",
        customer_id="CUST-111",
        total=349.99,
        currency="EUR",
        created_by="alice@example.com",
    )
    print(f"\n🔵 Event already at v3:")
    print(f"  • order_id: {event_v3_existing.order_id}")
    print(f"  • created_by: {event_v3_existing.created_by}")

    result = await registry.upcast(event_v3_existing, "OrderCreated", target_version=3)
    print(f"\n🔵 After 'upcasting' to v3 (no change):")
    print(f"  • Same object returned: {result is event_v3_existing}")

    # Scenario 5: Error handling - incomplete chain
    print("\n" + "=" * 70)
    print("SCENARIO 5: Error handling - incomplete upcasting chain")
    print("=" * 70)

    # Create new registry without v2→v3 upcaster
    incomplete_registry = UpcasterRegistry()
    incomplete_registry.register("OrderCreated", OrderCreatedV1toV2())
    # Missing v2→v3 upcaster!

    event_incomplete = OrderCreatedV1(
        order_id="ORD-005", customer_id="CUST-222", total=199.99
    )

    try:
        await incomplete_registry.upcast(
            event_incomplete, "OrderCreated", target_version=3
        )
    except Exception as e:
        print(f"\n❌ Error (expected): {type(e).__name__}")
        print(f"   Message: {str(e)}")

    print("\n" + "=" * 70)
    print("✅ Event versioning example complete")
    print("=" * 70)
    print("""
Key insights:
1. ✓ Events automatically upgrade through chained upcasters
2. ✓ Old events in storage seamlessly migrate to new schema
3. ✓ Multi-step chains (v1→v2→v3) work transparently
4. ✓ Supports intermediate versions if needed
5. ✓ Downcasting prevented (data loss safety)
6. ✓ Errors caught if migration chain incomplete

Production benefits:
• Zero downtime schema evolution
• Backward compatibility with old events
• Gradual migration of event store
• Type-safe transformations
• Audit trail of changes
    """)


if __name__ == "__main__":
    asyncio.run(main())
