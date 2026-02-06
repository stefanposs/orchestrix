"""SLA Monitoring Projection — Observability Read Model.

Builds a live read model from the event stream that tracks:
    - Dataset freshness status
    - SLA violation history
    - Time-to-publish metrics per dataset
    - Overall platform health score

This projection subscribes to events from the InMemoryEventStore
and updates in-memory counters. In production, this would write
to a time-series database or metrics backend.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

logger = logging.getLogger("lakehouse.sla_monitor")


@dataclass
class DatasetHealth:
    """Health summary for a single dataset."""

    dataset: str = ""
    total_batches: int = 0
    published_batches: int = 0
    quarantined_batches: int = 0
    validated_batches: int = 0
    sla_checks: int = 0
    sla_breaches: int = 0
    last_publish_at: datetime | None = None
    last_ingest_at: datetime | None = None
    last_breach_at: datetime | None = None
    execution_count: int = 0
    execution_failures: int = 0
    avg_execution_seconds: float = 0.0
    _total_execution_seconds: float = 0.0

    @property
    def sla_compliance_pct(self) -> float:
        """SLA compliance as percentage (0-100)."""
        if self.sla_checks == 0:
            return 100.0
        return round((1.0 - self.sla_breaches / self.sla_checks) * 100, 2)

    @property
    def publish_rate_pct(self) -> float:
        """Percentage of batches that reached PUBLISHED state."""
        if self.total_batches == 0:
            return 0.0
        return round(self.published_batches / self.total_batches * 100, 2)

    @property
    def quarantine_rate_pct(self) -> float:
        """Percentage of batches that were quarantined."""
        if self.total_batches == 0:
            return 0.0
        return round(self.quarantined_batches / self.total_batches * 100, 2)


@dataclass
class PlatformMetrics:
    """Aggregate platform-level metrics."""

    total_datasets: int = 0
    total_slas: int = 0
    total_breaches: int = 0
    total_executions: int = 0
    total_execution_failures: int = 0
    datasets: dict[str, DatasetHealth] = field(default_factory=dict)

    def health_score(self) -> float:
        """Overall platform health score (0-100).

        Weighted average of SLA compliance and publish rate across
        all datasets.
        """
        if not self.datasets:
            return 100.0
        scores = []
        for dh in self.datasets.values():
            # 60% weight on SLA compliance, 40% on publish rate
            score = 0.6 * dh.sla_compliance_pct + 0.4 * dh.publish_rate_pct
            scores.append(score)
        return round(sum(scores) / len(scores), 2)


class SLAMonitor:
    """Event-driven SLA monitoring projection.

    Call ``handle_event()`` for each event emitted by the system.
    The monitor builds up ``PlatformMetrics`` that can be queried
    by the API layer.

    Usage::

        monitor = SLAMonitor()

        # After each event_store.save():
        for event in new_events:
            monitor.handle_event(event)

        # Query:
        metrics = monitor.metrics
        health = monitor.get_dataset_health("sales")
    """

    def __init__(self) -> None:
        self._metrics = PlatformMetrics()
        self._handlers: dict[str, object] = {
            "DatasetRegistered": self._on_dataset_registered,
            "DataAppended": self._on_data_appended,
            "DataPublished": self._on_data_published,
            "BatchQuarantined": self._on_batch_quarantined,
            "QualityCheckPassed": self._on_quality_check_passed,
            "SLADefined": self._on_sla_defined,
            "SLACheckPassed": self._on_sla_check_passed,
            "SLABreached": self._on_sla_breached,
            "ExecutionCompleted": self._on_execution_completed,
            "ExecutionFailed": self._on_execution_failed,
        }

    @property
    def metrics(self) -> PlatformMetrics:
        """Return current platform metrics."""
        return self._metrics

    def get_dataset_health(self, dataset: str) -> DatasetHealth | None:
        """Return health metrics for a specific dataset."""
        return self._metrics.datasets.get(dataset)

    def handle_event(self, event: object) -> None:
        """Route an event to its handler (if any)."""
        event_type = type(event).__name__
        handler = self._handlers.get(event_type)
        if handler is not None:
            handler(event)  # type: ignore[operator]

    def _ensure_dataset(self, dataset: str) -> DatasetHealth:
        """Get or create DatasetHealth for a given dataset."""
        if dataset not in self._metrics.datasets:
            self._metrics.datasets[dataset] = DatasetHealth(dataset=dataset)
        return self._metrics.datasets[dataset]

    # -- Event handlers --

    def _on_dataset_registered(self, event: object) -> None:
        name = getattr(event, "name", "")
        self._ensure_dataset(name)
        self._metrics.total_datasets += 1

    def _on_data_appended(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        dh = self._ensure_dataset(dataset)
        dh.total_batches += 1
        dh.last_ingest_at = datetime.now(UTC)

    def _on_data_published(self, event: object) -> None:
        # Try to find the dataset from the event — fall back to scanning
        dataset = getattr(event, "dataset", "")
        if dataset:
            dh = self._ensure_dataset(dataset)
            dh.published_batches += 1
            dh.last_publish_at = datetime.now(UTC)

    def _on_batch_quarantined(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        if dataset:
            dh = self._ensure_dataset(dataset)
            dh.quarantined_batches += 1

    def _on_quality_check_passed(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        if dataset:
            dh = self._ensure_dataset(dataset)
            dh.validated_batches += 1

    def _on_sla_defined(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        self._ensure_dataset(dataset)
        self._metrics.total_slas += 1

    def _on_sla_check_passed(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        dh = self._ensure_dataset(dataset)
        dh.sla_checks += 1

    def _on_sla_breached(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        dh = self._ensure_dataset(dataset)
        dh.sla_checks += 1
        dh.sla_breaches += 1
        dh.last_breach_at = datetime.now(UTC)
        self._metrics.total_breaches += 1

    def _on_execution_completed(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        duration = getattr(event, "duration_seconds", 0.0)
        dh = self._ensure_dataset(dataset)
        dh.execution_count += 1
        dh._total_execution_seconds += duration
        dh.avg_execution_seconds = round(dh._total_execution_seconds / dh.execution_count, 4)
        self._metrics.total_executions += 1

    def _on_execution_failed(self, event: object) -> None:
        dataset = getattr(event, "dataset", "")
        dh = self._ensure_dataset(dataset)
        dh.execution_count += 1
        dh.execution_failures += 1
        self._metrics.total_executions += 1
        self._metrics.total_execution_failures += 1
