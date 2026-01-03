"""Example: Distributed tracing with Jaeger for order processing.

Demonstrates how to trace events, commands, and sagas across microservice
boundaries using Jaeger and OpenTelemetry. Automatic context propagation
allows tracking requests end-to-end.

Scenario:
- Order creation event traced
- Confirmation command traced
- Payment saga traced with multiple steps
- All traces correlated via trace ID
"""

import asyncio
from dataclasses import dataclass

from orchestrix.core.message import Event
from orchestrix.infrastructure.tracing import JaegerTracer, TracingConfig, init_tracing


@dataclass(frozen=True)
class OrderCreated(Event):
    """Event for order creation."""

    order_id: str
    customer_id: str
    total: float


@dataclass(frozen=True)
class OrderConfirmed(Event):
    """Event for order confirmation."""

    order_id: str


@dataclass(frozen=True)
class PaymentProcessed(Event):
    """Event for payment processing."""

    order_id: str
    amount: float


async def main() -> None:
    """Demonstrate distributed tracing with Jaeger."""

    print("=" * 70)
    print("DISTRIBUTED TRACING WITH JAEGER EXAMPLE")
    print("=" * 70)

    print("\n📊 Initializing Jaeger tracing...")
    print("  Note: Requires Jaeger agent running on localhost:6831")
    print("  Start with: docker run -d -p 6831:6831/udp jaegertracing/all-in-one")

    try:
        # Initialize tracing
        config = TracingConfig(
            service_name="order-service",
            jaeger_agent_host="localhost",
            jaeger_agent_port=6831,
        )
        tracer = init_tracing(config=config)
        print("  ✓ Tracing initialized")
    except ImportError:
        print("  ⚠ Jaeger not installed, using mock tracer")
        tracer = JaegerTracer()

    # Scenario 1: Trace event processing
    print("\n" + "=" * 70)
    print("SCENARIO 1: TRACING EVENT PROCESSING")
    print("=" * 70)

    print("\n🔴 Creating order event...")
    with tracer.span_event(
        event_type="OrderCreated",
        event_id="evt-001",
        aggregate_id="order-123",
    ):
        tracer.set_attribute("customer_id", "cust-456")
        tracer.set_attribute("total", 99.99)
        tracer.set_attribute("currency", "USD")
        tracer.add_event("order_created")

        print("  ✓ Event traced:")
        print("    - Event Type: OrderCreated")
        print("    - Event ID: evt-001")
        print("    - Aggregate ID: order-123")
        trace_id = tracer.get_trace_id()
        if trace_id:
            print(f"    - Trace ID: {trace_id}")

    # Scenario 2: Trace command handling
    print("\n" + "=" * 70)
    print("SCENARIO 2: TRACING COMMAND HANDLING")
    print("=" * 70)

    print("\n🟢 Processing confirmation command...")
    with tracer.span_command(
        command_type="ConfirmOrder", aggregate_id="order-123"
    ):
        tracer.set_attribute("status", "pending_payment")
        tracer.add_event("command_received")
        tracer.add_event("validation_passed")

        print("  ✓ Command traced:")
        print("    - Command: ConfirmOrder")
        print("    - Aggregate: order-123")
        print("    - Events: command_received, validation_passed")

    # Scenario 3: Trace async saga execution
    print("\n" + "=" * 70)
    print("SCENARIO 3: TRACING ASYNC SAGA EXECUTION")
    print("=" * 70)

    async def execute_payment_saga() -> None:
        """Execute payment saga with nested spans."""
        with tracer.span_saga(saga_type="PaymentProcessing", saga_id="saga-001"):
            tracer.set_attribute("order_id", "order-123")
            tracer.set_attribute("amount", 99.99)

            # Step 1: Debit account
            print("\n  Step 1: Debit account...")
            async with tracer.async_span(
                "debit_account", {"account": "ACC-001"}
            ):
                await asyncio.sleep(0.01)
                tracer.add_event("debit_successful")
                print("    ✓ Account debited")

            # Step 2: Credit merchant
            print("\n  Step 2: Credit merchant...")
            async with tracer.async_span(
                "credit_merchant", {"merchant": "MERCHANT-999"}
            ):
                await asyncio.sleep(0.01)
                tracer.add_event("credit_successful")
                print("    ✓ Merchant credited")

            # Step 3: Generate invoice
            print("\n  Step 3: Generate invoice...")
            async with tracer.async_span("generate_invoice"):
                await asyncio.sleep(0.01)
                tracer.set_attribute("invoice_id", "INV-2024-001")
                tracer.add_event("invoice_generated")
                print("    ✓ Invoice generated")

            tracer.add_event("saga_completed")

    print("\n🔀 Executing payment saga...")
    await execute_payment_saga()
    print("\n  ✓ Saga execution traced with 3 nested spans")

    # Scenario 4: Trace multiple concurrent operations
    print("\n" + "=" * 70)
    print("SCENARIO 4: MULTIPLE CONCURRENT TRACES")
    print("=" * 70)

    async def process_order(order_id: str, amount: float) -> None:
        """Process single order with tracing."""
        with tracer.span_command(command_type="ProcessOrder", aggregate_id=order_id):
            tracer.set_attribute("amount", amount)
            await asyncio.sleep(0.01)
            tracer.add_event("order_processed")

    print("\n📦 Processing multiple orders concurrently...")
    await asyncio.gather(
        process_order("order-100", 49.99),
        process_order("order-101", 99.99),
        process_order("order-102", 199.99),
    )
    print("  ✓ All 3 orders traced with correlation")

    # Scenario 5: Trace error scenarios
    print("\n" + "=" * 70)
    print("SCENARIO 5: ERROR TRACING")
    print("=" * 70)

    print("\n❌ Processing failed order...")
    try:
        with tracer.span(
            "process_invalid_order", {"order_id": "invalid-123"}
        ):
            tracer.set_attribute("validation_status", "failed")
            raise ValueError("Invalid order format")
    except ValueError as e:
        print(f"  ✓ Error traced: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("✅ DISTRIBUTED TRACING EXAMPLE COMPLETE")
    print("=" * 70)
    print("""
Trace Features Demonstrated:
1. ✓ Event-level tracing with attributes
2. ✓ Command handling with status tracking
3. ✓ Async saga execution with nested spans
4. ✓ Concurrent operations with correlation
5. ✓ Error tracking with exception details

Production Integration:
• View traces at: http://localhost:16686 (Jaeger UI)
• Filter by service: order-service
• Search by trace ID
• Analyze latency and dependencies
• Set up alerts on slow operations

Trace Structure:
order-service
├── Event: OrderCreated
├── Command: ConfirmOrder
├── Saga: PaymentProcessing
│   ├── Span: debit_account
│   ├── Span: credit_merchant
│   └── Span: generate_invoice
├── Orders (concurrent)
│   ├── ProcessOrder: order-100
│   ├── ProcessOrder: order-101
│   └── ProcessOrder: order-102
└── Error: process_invalid_order
    """)


if __name__ == "__main__":
    asyncio.run(main())
