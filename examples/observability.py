"""Observability Example: Metrics and Tracing for Event Sourcing.

This example demonstrates how to integrate observability hooks into your
event sourcing application using custom metrics and tracing providers.

Features:
- Event processing metrics (counts, latencies)
- Distributed tracing with causation tracking
- Error tracking and alerts
- Health monitoring dashboards
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from orchestrix.core import (
    AggregateRepository,
    AggregateRoot,
    Event,
    MetricsProvider,
    TracingProvider,
    TraceSpan,
    init_observability,
)
from orchestrix.infrastructure.async_inmemory_store import InMemoryAsyncEventStore
from orchestrix.infrastructure.async_inmemory_bus import InMemoryAsyncMessageBus


# ============================================================================
# 1. Custom Metrics Provider (simulating Prometheus)
# ============================================================================


class SimpleMetricsProvider(MetricsProvider):
    """Simple in-memory metrics provider for demonstration.

    In production, replace with Prometheus, DataDog, or CloudWatch.
    """

    def __init__(self):
        """Initialize metrics storage."""
        self.metrics: dict[str, dict] = {
            "counters": {},
            "gauges": {},
            "histograms": {},
        }

    def record_metric(self, metric):
        """Record a metric value."""
        key = f"{metric.name}:{metric.metric_type}"
        self.metrics["counters"][key] = self.metrics["counters"].get(key, 0) + 1

    def counter(self, name: str, value: float = 1.0, labels=None):
        """Record counter metric."""
        key = f"{name}:{','.join(f'{k}={v}' for k, v in (labels or {}).items())}"
        self.metrics["counters"][key] = self.metrics["counters"].get(key, 0) + value
        print(f"📊 COUNTER: {key} = {self.metrics['counters'][key]}")

    def gauge(self, name: str, value: float, labels=None):
        """Record gauge metric."""
        key = f"{name}:{','.join(f'{k}={v}' for k, v in (labels or {}).items())}"
        self.metrics["gauges"][key] = value
        print(f"📏 GAUGE: {key} = {value}")

    def histogram(self, name: str, value: float, unit: str = "", labels=None):
        """Record histogram metric."""
        key = f"{name}:{','.join(f'{k}={v}' for k, v in (labels or {}).items())}"
        if key not in self.metrics["histograms"]:
            self.metrics["histograms"][key] = []
        self.metrics["histograms"][key].append(value)
        print(f"📈 HISTOGRAM: {key} = {value}{unit}")

    def get_stats(self, name: str) -> dict:
        """Get statistics for a histogram."""
        if name in self.metrics["histograms"]:
            values = self.metrics["histograms"][name]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values) if values else 0,
            }
        return {}


# ============================================================================
# 2. Custom Tracing Provider (simulating Jaeger)
# ============================================================================


class SimpleTracingProvider(TracingProvider):
    """Simple distributed tracing provider for demonstration.

    In production, replace with Jaeger, Zipkin, or DataDog.
    """

    def __init__(self):
        """Initialize trace storage."""
        self.spans: list[TraceSpan] = []
        self.trace_id = 0

    def start_span(self, operation: str) -> TraceSpan:
        """Start a new trace span."""
        span = TraceSpan(operation=operation)
        self.trace_id += 1
        print(f"🔄 START SPAN [{self.trace_id}]: {operation}")
        return span

    def end_span(self, span: TraceSpan) -> None:
        """End a trace span."""
        span.end()
        self.spans.append(span)
        print(f"✓ END SPAN: {span.operation} ({span.duration_ms:.2f}ms) - {span.status}")

    def get_trace_summary(self) -> dict:
        """Get summary of all traces."""
        return {
            "total_spans": len(self.spans),
            "avg_duration_ms": sum(s.duration_ms for s in self.spans) / len(self.spans)
            if self.spans
            else 0,
            "error_spans": sum(1 for s in self.spans if s.status == "error"),
        }


# ============================================================================
# 3. Domain Model: Bank Account
# ============================================================================


@dataclass(frozen=True)
class MoneyDeposited(Event):
    """Money was deposited into the account."""

    account_id: str = ""
    amount: float = 0.0


@dataclass(frozen=True)
class MoneyWithdrawn(Event):
    """Money was withdrawn from the account."""

    account_id: str = ""
    amount: float = 0.0


@dataclass
class BankAccount(AggregateRoot):
    """Bank account aggregate with balance tracking."""

    account_number: str = ""
    balance: float = 0.0
    transactions: list[dict] = field(default_factory=list)

    def deposit(self, amount: float) -> None:
        """Deposit money into account."""
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self._apply_event(
            MoneyDeposited(
                account_id=self.aggregate_id,
                amount=amount,
            )
        )

    def withdraw(self, amount: float) -> None:
        """Withdraw money from account."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds")

        self._apply_event(
            MoneyWithdrawn(
                account_id=self.aggregate_id,
                amount=amount,
            )
        )

    def _when_money_deposited(self, event: Event) -> None:
        """Handle money deposited event."""
        # Access via dictionary since CloudEvents format
        event_data = vars(event) if hasattr(event, '__dict__') else event
        amount = event_data.get("amount", 0) if isinstance(event_data, dict) else getattr(event, 'amount', 0)
        
        self.balance += amount
        self.transactions.append({
            "type": "deposit",
            "amount": amount,
            "balance": self.balance,
        })
        print(f"  💰 Deposit: ${amount:.2f} (balance: ${self.balance:.2f})")

    def _when_money_withdrawn(self, event: Event) -> None:
        """Handle money withdrawn event."""
        # Access via dictionary since CloudEvents format
        event_data = vars(event) if hasattr(event, '__dict__') else event
        amount = event_data.get("amount", 0) if isinstance(event_data, dict) else getattr(event, 'amount', 0)
        
        self.balance -= amount
        self.transactions.append({
            "type": "withdrawal",
            "amount": amount,
            "balance": self.balance,
        })
        print(f"  💸 Withdrawal: ${amount:.2f} (balance: ${self.balance:.2f})")


# ============================================================================
# 4. Setup Observability
# ============================================================================


async def main():
    """Run observability example."""

    print("\n" + "=" * 70)
    print("ORCHESTRIX OBSERVABILITY EXAMPLE")
    print("=" * 70 + "\n")

    # Initialize metrics and tracing providers
    metrics = SimpleMetricsProvider()
    tracing = SimpleTracingProvider()

    # Initialize observability
    observability = init_observability(
        metrics_provider=metrics,
        tracing_provider=tracing,
    )

    # Register callbacks for additional tracking
    def on_event_stored(agg_id: str, version: int):
        print(f"  → Event stored: {agg_id} v{version}")

    def on_error(agg_id: str, error: str):
        print(f"  ⚠️  ERROR in {agg_id}: {error}")

    observability.on_event_stored(on_event_stored)
    observability.on_aggregate_error(on_error)

    # Create repository with async event store
    store = InMemoryAsyncEventStore()
    repository = AggregateRepository(store)

    print("✓ Observability initialized with metrics and tracing providers\n")

    # ========================================================================
    # 5. Scenario 1: Create and Use Bank Account
    # ========================================================================

    print("📌 SCENARIO 1: Bank Account Operations")
    print("-" * 70)

    # Create new account
    account = BankAccount(
        aggregate_id="account-001",
        account_number="ACC-12345",
        balance=0.0,
    )

    # Simulate operations
    print("\n→ Creating account...")
    account.deposit(1000.0)
    await repository.save_async(account)

    print("\n→ Depositing $500...")
    account.deposit(500.0)
    await repository.save_async(account)

    print("\n→ Withdrawing $200...")
    account.withdraw(200.0)
    await repository.save_async(account)

    # Load account to trigger event replay
    print("\n→ Loading account from event store...")
    span = observability.start_event_store_operation("load")
    loaded_account = await repository.load_async(BankAccount, "account-001")
    observability.end_event_store_operation(span)

    print(f"\n✓ Loaded account: balance = ${loaded_account.balance:.2f}")
    print(f"  Transactions: {len(loaded_account.transactions)}")

    # ========================================================================
    # 6. Scenario 2: Multiple Operations with Error Handling
    # ========================================================================

    print("\n\n📌 SCENARIO 2: Multiple Accounts and Error Handling")
    print("-" * 70)

    accounts_data = [
        ("account-002", "ACC-22345", 500.0),
        ("account-003", "ACC-33345", 1500.0),
    ]

    for agg_id, acc_num, initial_deposit in accounts_data:
        print(f"\n→ Processing {acc_num}...")

        account = BankAccount(aggregate_id=agg_id, account_number=acc_num)
        account.deposit(initial_deposit)
        await repository.save_async(account)

        # Try invalid withdrawal
        try:
            account.withdraw(3000.0)
            await repository.save_async(account)
        except ValueError as e:
            print(f"  ⚠️  Invalid withdrawal: {e}")
            observability.record_aggregate_error(agg_id, str(e))

        # Valid withdrawal
        account.withdraw(200.0)
        await repository.save_async(account)

    # ========================================================================
    # 7. Performance Analysis
    # ========================================================================

    print("\n\n📌 SCENARIO 3: Performance Analysis")
    print("-" * 70)

    print("\n→ Running 50 concurrent deposit operations...")
    start_time = time.time()

    async def concurrent_deposit(acc_id: str, amount: float):
        account = BankAccount(aggregate_id=acc_id)
        account.deposit(amount)
        await repository.save_async(account)

    tasks = [
        concurrent_deposit(f"account-perf-{i}", 100.0 + i)
        for i in range(50)
    ]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    print(f"✓ Completed 50 operations in {elapsed:.3f}s ({50/elapsed:.1f} ops/sec)")

    # ========================================================================
    # 8. Observability Report
    # ========================================================================

    print("\n\n" + "=" * 70)
    print("OBSERVABILITY REPORT")
    print("=" * 70)

    print("\n📊 METRICS:")
    print("-" * 70)
    for key, value in metrics.metrics["counters"].items():
        print(f"  {key}: {value}")

    print("\n🔄 TRACING:")
    print("-" * 70)
    trace_summary = tracing.get_trace_summary()
    print(f"  Total Spans: {trace_summary['total_spans']}")
    print(f"  Average Duration: {trace_summary['avg_duration_ms']:.2f}ms")
    print(f"  Error Spans: {trace_summary['error_spans']}")

    print("\n✅ Full traces available for analysis and debugging")
    print("   → Use these to identify bottlenecks")
    print("   → Track causation IDs for distributed tracing")
    print("   → Monitor error rates per operation type\n")


if __name__ == "__main__":
    asyncio.run(main())
