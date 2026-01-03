"""Example: Prometheus metrics integration for observability.

This example demonstrates production-grade monitoring using Prometheus metrics
for event sourcing systems. Track events, commands, aggregates, and storage
operations with comprehensive observability.

Scenario:
- Initialize Prometheus metrics with custom namespace
- Track event publishing, command handling, aggregate loading
- Monitor storage operations and projections
- Generate Prometheus exposition format for scraping
"""

import asyncio
from dataclasses import dataclass

from orchestrix.core.message import Event
from orchestrix.infrastructure.prometheus_metrics import (
    MetricConfig,
    MetricOperationType,
    PrometheusMetrics,
)


@dataclass(frozen=True)
class OrderCreated(Event):
    """Sample event for demonstration."""

    order_id: str
    customer_id: str
    total: float


@dataclass(frozen=True)
class OrderConfirmed(Event):
    """Sample event for demonstration."""

    order_id: str


async def main() -> None:
    """Demonstrate Prometheus metrics integration."""

    print("=" * 70)
    print("PROMETHEUS METRICS INTEGRATION EXAMPLE")
    print("=" * 70)

    # Configure metrics with custom namespace
    config = MetricConfig(
        namespace="ecommerce", subsystem="orders", enable_summary_metrics=True
    )
    metrics = PrometheusMetrics(config=config)

    print("\n📊 Metrics initialized:")
    print(f"  • Namespace: {config.namespace}")
    print(f"  • Subsystem: {config.subsystem}")
    print(f"  • Summary metrics: {config.enable_summary_metrics}")

    # Simulate event publishing
    print("\n" + "=" * 70)
    print("TRACKING EVENT PUBLISHING")
    print("=" * 70)

    events_to_publish = [
        ("OrderCreated", 10),
        ("OrderConfirmed", 8),
        ("PaymentProcessed", 5),
    ]

    for event_type, count in events_to_publish:
        print(f"\n📤 Publishing {count} {event_type} events...")
        for i in range(count):
            try:
                with metrics.track_event_publish(event_type=event_type):
                    # Simulate publish delay
                    await asyncio.sleep(0.001)
            except Exception as e:
                print(f"  ❌ Error publishing: {e}")

    print(f"  ✓ Published {count} {event_type} events")

    # Simulate command handling
    print("\n" + "=" * 70)
    print("TRACKING COMMAND HANDLING")
    print("=" * 70)

    commands = [
        ("CreateOrder", 5),
        ("ConfirmOrder", 3),
        ("CancelOrder", 1),
    ]

    for cmd_type, count in commands:
        print(f"\n🎯 Handling {count} {cmd_type} commands...")
        for i in range(count):
            try:
                with metrics.track_command_handle(command_type=cmd_type):
                    await asyncio.sleep(0.001)
            except Exception as e:
                print(f"  ❌ Error handling: {e}")

        print(f"  ✓ Handled {count} {cmd_type} commands")

    # Simulate aggregate loading
    print("\n" + "=" * 70)
    print("TRACKING AGGREGATE LOADING")
    print("=" * 70)

    aggregates = [
        ("Order", 15),
        ("Customer", 10),
        ("Payment", 8),
    ]

    for agg_type, count in aggregates:
        print(f"\n🏗️  Loading {count} {agg_type} aggregates...")
        for i in range(count):
            try:
                with metrics.track_aggregate_load(aggregate_type=agg_type):
                    await asyncio.sleep(0.0005)
            except Exception as e:
                print(f"  ❌ Error loading: {e}")

        print(f"  ✓ Loaded {count} {agg_type} aggregates")

    # Simulate storage operations
    print("\n" + "=" * 70)
    print("TRACKING STORAGE OPERATIONS")
    print("=" * 70)

    operations = [
        (MetricOperationType.APPEND, 20, "Appending events"),
        (MetricOperationType.LOAD, 15, "Loading events"),
        (MetricOperationType.DELETE, 2, "Deleting events"),
    ]

    for op_type, count, description in operations:
        print(f"\n💾 {description}...")
        for i in range(count):
            try:
                with metrics.track_storage_operation(operation_type=op_type):
                    await asyncio.sleep(0.0005)
            except Exception as e:
                print(f"  ❌ Error: {e}")

        print(f"  ✓ {description}")

    # Simulate projection lag tracking
    print("\n" + "=" * 70)
    print("TRACKING PROJECTION LAG")
    print("=" * 70)

    projections = {
        "OrderSummary": 42,
        "CustomerProfile": 7,
        "PaymentStatus": 0,
    }

    print("\n📈 Recording projection lag...")
    for proj_name, lag in projections.items():
        metrics.record_projection_lag(proj_name, lag)
        print(f"  • {proj_name}: {lag} events behind")

    # Simulate projection updates
    print("\n" + "=" * 70)
    print("TRACKING PROJECTION UPDATES")
    print("=" * 70)

    for proj_name in projections.keys():
        print(f"\n🔄 Updating {proj_name}...")
        try:
            with metrics.track_projection_update(projection_name=proj_name):
                await asyncio.sleep(0.001)
            print(f"  ✓ Updated {proj_name}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Simulate saga execution
    print("\n" + "=" * 70)
    print("TRACKING SAGA EXECUTION")
    print("=" * 70)

    sagas = [
        ("MoneyTransfer", 5),
        ("OrderFulfillment", 3),
    ]

    for saga_type, count in sagas:
        print(f"\n🔀 Executing {count} {saga_type} sagas...")
        for i in range(count):
            try:
                with metrics.track_saga_execution(saga_type=saga_type):
                    await asyncio.sleep(0.001)
            except Exception as e:
                print(f"  ❌ Error: {e}")

        print(f"  ✓ Executed {count} {saga_type} sagas")

    # Generate Prometheus exposition format
    print("\n" + "=" * 70)
    print("PROMETHEUS EXPOSITION FORMAT")
    print("=" * 70)

    exposition = PrometheusMetrics.generate_exposition(metrics.get_prometheus_registry())

    # Display excerpt of exposition
    exposition_str = exposition.decode("utf-8")
    lines = exposition_str.split("\n")

    print("\n📋 Metrics generated (sample lines):")
    metric_lines = [l for l in lines if l and not l.startswith("#")][:15]
    for line in metric_lines:
        if "ecommerce_orders" in line:
            # Extract metric name and value
            parts = line.split("{")
            metric_name = parts[0]
            print(f"  • {metric_name}")

    total_metrics = len([l for l in lines if l and not l.startswith("#")])
    print(f"\n✓ Total metrics recorded: {total_metrics}")

    # Show metric types
    print("\n📊 Metric types in exposition:")
    metric_types = set()
    for line in lines:
        if "# TYPE" in line:
            parts = line.split()
            if len(parts) >= 3:
                metric_types.add(parts[-1])

    for mtype in sorted(metric_types):
        count = len([l for l in lines if f"# TYPE" in l and mtype in l])
        print(f"  • {mtype.upper()}: {count} metrics")

    print("\n" + "=" * 70)
    print("✅ Prometheus metrics example complete")
    print("=" * 70)
    print("""
Key insights:
1. ✓ Context managers simplify metric tracking
2. ✓ Both sync and async tracking supported
3. ✓ Success/failure automatically recorded
4. ✓ Latency histograms for performance monitoring
5. ✓ Gauge metrics for lag tracking
6. ✓ Custom namespace for multi-tenant systems

Production integration:
• Expose metrics on /metrics endpoint
• Configure Prometheus scraper (prometheus.yml)
• Create Grafana dashboards for visualization
• Set up alerts on critical metrics
• Monitor event processing latency, error rates
    """)


if __name__ == "__main__":
    asyncio.run(main())
