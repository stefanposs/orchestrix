"""Executor Layer — Pluggable multi-backend job execution.

The Executor Layer abstracts job execution (validation, anonymization,
publish) behind a common Protocol so backends can be swapped without
changing the control-plane logic.

Supported backends:
    - LocalPythonExecutor   — in-process Python (dev / testing)
    - BigQueryExecutor      — stub for BigQuery SQL jobs
    - SparkExecutor         — stub for PySpark / Databricks
    - DbtExecutor           — stub for dbt model runs

The ``ExecutorRegistry`` maps executor type strings to implementations.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

logger = logging.getLogger("lakehouse.executor")


# ---------------------------------------------------------------------------
# Executor Protocol — every backend must satisfy this
# ---------------------------------------------------------------------------


class Executor(Protocol):
    """Protocol for job executors.

    Executors receive a job description, run the task, and return
    a result dict.  The control-plane (entry.py) always wraps calls
    in event-sourced aggregates so the result is persisted.
    """

    def execute(self, job_type: str, parameters: dict[str, Any]) -> ExecutorResult:
        """Run a job and return the result."""
        ...


@dataclass(frozen=True)
class ExecutorResult:
    """Immutable result from an executor run."""

    success: bool
    result: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    executor_type: str = "unknown"


# ---------------------------------------------------------------------------
# Local Python Executor — runs validation / anonymization in-process
# ---------------------------------------------------------------------------


class LocalPythonExecutor:
    """In-process Python executor for development and testing.

    Simulates validation, anonymization, and publish jobs with
    deterministic results so the demo pipeline is fully exercisable
    without external dependencies.
    """

    def execute(self, job_type: str, parameters: dict[str, Any]) -> ExecutorResult:
        """Dispatch to the appropriate handler based on ``job_type``."""
        start = time.monotonic()
        handler = {
            "validation": self._validate,
            "anonymization": self._anonymize,
            "publish": self._publish,
        }.get(job_type)

        if handler is None:
            return ExecutorResult(
                success=False,
                errors=[f"Unknown job type: {job_type}"],
                executor_type="local_python",
            )

        try:
            result = handler(parameters)
            duration = time.monotonic() - start
            return ExecutorResult(
                success=True,
                result=result,
                duration_seconds=round(duration, 4),
                executor_type="local_python",
            )
        except Exception as exc:
            duration = time.monotonic() - start
            return ExecutorResult(
                success=False,
                errors=[str(exc)],
                duration_seconds=round(duration, 4),
                executor_type="local_python",
            )

    # -- Job handlers ------------------------------------------------------

    @staticmethod
    def _validate(params: dict[str, Any]) -> dict[str, Any]:
        """Simulate data quality validation.

        Checks for required quality_rules and returns a pass/fail result
        with details per rule.
        """
        quality_rules = params.get("quality_rules", {})
        errors: list[str] = []
        checked: list[str] = []

        for field_name, rule in quality_rules.items():
            checked.append(field_name)
            # Simulate: rules starting with "!" always fail (for demo purposes)
            if isinstance(rule, str) and rule.startswith("!"):
                errors.append(f"Rule failed for '{field_name}': {rule}")

        sla_ok = not errors
        return {
            "status": "PASSED" if not errors else "FAILED",
            "rules_checked": checked,
            "errors": errors,
            "sla_ok": sla_ok,
            "rows_scanned": params.get("row_count", 10000),
        }

    @staticmethod
    def _anonymize(params: dict[str, Any]) -> dict[str, Any]:
        """Simulate data anonymization.

        Applies privacy rules and returns affected-row counts.
        """
        privacy_rules = params.get("privacy_rules", {})
        columns_processed = list(privacy_rules.keys())
        return {
            "status": "ANONYMIZED",
            "columns_processed": columns_processed,
            "rows_affected": params.get("row_count", 5000),
            "strategies_applied": dict(privacy_rules.items()),
        }

    @staticmethod
    def _publish(params: dict[str, Any]) -> dict[str, Any]:
        """Simulate publishing a dataset to the consumption layer."""
        return {
            "status": "PUBLISHED",
            "target": params.get("target", "data-lake-gold"),
            "publish_id": f"pub-{uuid.uuid4().hex[:8]}",
            "published_at": datetime.now(UTC).isoformat(),
        }


# ---------------------------------------------------------------------------
# Stub Executors — ready for real implementation
# ---------------------------------------------------------------------------


class BigQueryExecutor:
    """BigQuery executor stub.

    In production this would submit SQL jobs via the BigQuery API
    and poll for completion.
    """

    def execute(self, job_type: str, parameters: dict[str, Any]) -> ExecutorResult:
        """Simulate BigQuery execution."""
        logger.info("BigQueryExecutor: %s (stub)", job_type)
        return ExecutorResult(
            success=True,
            result={
                "status": "COMPLETED",
                "engine": "bigquery",
                "job_type": job_type,
                "bq_job_id": f"bq-{uuid.uuid4().hex[:8]}",
            },
            duration_seconds=1.5,
            executor_type="bigquery",
        )


class SparkExecutor:
    """Spark / Databricks executor stub.

    In production this would submit PySpark jobs to a Spark cluster
    or Databricks workspace.
    """

    def execute(self, job_type: str, parameters: dict[str, Any]) -> ExecutorResult:
        """Simulate Spark execution."""
        logger.info("SparkExecutor: %s (stub)", job_type)
        return ExecutorResult(
            success=True,
            result={
                "status": "COMPLETED",
                "engine": "spark",
                "job_type": job_type,
                "spark_app_id": f"spark-{uuid.uuid4().hex[:8]}",
            },
            duration_seconds=3.0,
            executor_type="spark",
        )


class DbtExecutor:
    """dbt executor stub.

    In production this would invoke ``dbt run`` or ``dbt test``
    for the specified model.
    """

    def execute(self, job_type: str, parameters: dict[str, Any]) -> ExecutorResult:
        """Simulate dbt execution."""
        logger.info("DbtExecutor: %s (stub)", job_type)
        return ExecutorResult(
            success=True,
            result={
                "status": "COMPLETED",
                "engine": "dbt",
                "job_type": job_type,
                "dbt_run_id": f"dbt-{uuid.uuid4().hex[:8]}",
            },
            duration_seconds=2.0,
            executor_type="dbt",
        )


# ---------------------------------------------------------------------------
# Executor Registry — maps type strings to implementations
# ---------------------------------------------------------------------------


class ExecutorRegistry:
    """Central registry for executors.

    Maps executor type names to concrete implementations::

        registry = ExecutorRegistry()
        registry.register("bigquery", BigQueryExecutor())

        executor = registry.get("local_python")
        result = executor.execute("validation", {...})
    """

    def __init__(self) -> None:
        self._executors: dict[str, Executor] = {}

    def register(self, executor_type: str, executor: Executor) -> None:
        """Register an executor implementation."""
        self._executors[executor_type] = executor

    def get(self, executor_type: str) -> Executor:
        """Get an executor by type name.

        Raises:
            KeyError: If no executor is registered for the given type.
        """
        if executor_type not in self._executors:
            available = ", ".join(sorted(self._executors.keys())) or "(none)"
            msg = f"Unknown executor type '{executor_type}'. Available: {available}"
            raise KeyError(msg)
        return self._executors[executor_type]

    def available_types(self) -> list[str]:
        """Return list of registered executor type names."""
        return sorted(self._executors.keys())


# ---------------------------------------------------------------------------
# Default registry with all built-in executors
# ---------------------------------------------------------------------------


def create_default_registry() -> ExecutorRegistry:
    """Create an ExecutorRegistry pre-loaded with all built-in executors."""
    registry = ExecutorRegistry()
    registry.register("local_python", LocalPythonExecutor())
    registry.register("bigquery", BigQueryExecutor())
    registry.register("spark", SparkExecutor())
    registry.register("dbt", DbtExecutor())
    return registry
