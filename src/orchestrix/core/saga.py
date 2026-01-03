"""Saga Orchestration Framework for distributed transactions.

Sagas are long-running transactions that span multiple aggregates and services.
They use compensation-based rollback instead of traditional ACID transactions.

Pattern: Choreography vs Orchestration
- Choreography: Events trigger other events (distributed, complex error handling)
- Orchestration: Central saga orchestrator controls flow (easier to understand, single point of failure)

This implementation uses orchestration pattern for clarity and error handling.
"""

from __future__ import annotations

import asyncio
import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, Protocol, TypeVar

from orchestrix.core.message import Event
from orchestrix.core.observability import TracingProvider

# Type for saga actions and compensations
T = TypeVar("T")


class SagaStatus(str, Enum):
    """Status of a saga execution."""

    PENDING = "pending"
    """Saga has been created but not started"""

    IN_PROGRESS = "in_progress"
    """Saga is currently executing"""

    COMPLETED = "completed"
    """Saga completed successfully"""

    COMPENSATING = "compensating"
    """Saga is rolling back due to failure"""

    FAILED = "failed"
    """Saga failed and could not be compensated"""


@dataclass
class SagaStepStatus:
    """Status of a single saga step execution."""

    step_name: str
    """Name of the step"""

    status: str = "pending"
    """Current status: pending, completed, compensating, compensated, failed"""

    result: Optional[Any] = None
    """Result from the action"""

    error: Optional[str] = None
    """Error message if step failed"""

    started_at: Optional[datetime] = None
    """When the step started"""

    completed_at: Optional[datetime] = None
    """When the step completed"""


@dataclass(frozen=True, kw_only=True)
class SagaState:
    """State of a saga execution for recovery and monitoring."""

    saga_id: str
    """Unique saga identifier"""

    saga_type: str
    """Type of saga (e.g., 'MoneyTransfer')"""

    status: SagaStatus = SagaStatus.PENDING
    """Current saga status"""

    step_statuses: dict[str, SagaStepStatus] = field(default_factory=dict)
    """Status of each step"""

    current_step_index: int = 0
    """Index of currently executing step"""

    started_at: Optional[datetime] = field(default=None)
    """When the saga started"""

    completed_at: Optional[datetime] = field(default=None)
    """When the saga completed (success or failure)"""

    error: Optional[str] = field(default=None)
    """Error that caused saga to fail"""

    def is_completed(self) -> bool:
        """Check if saga is complete (success or failure)."""
        return self.status in (SagaStatus.COMPLETED, SagaStatus.FAILED)


class SagaStateStore(Protocol):
    """Stores saga state for recovery and monitoring."""

    @abstractmethod
    async def load_state(self, saga_id: str) -> Optional[SagaState]:
        """Load saga state.

        Args:
            saga_id: The saga identifier

        Returns:
            The saved state or None if not found
        """
        ...

    @abstractmethod
    async def save_state(self, state: SagaState) -> None:
        """Save saga state.

        Args:
            state: The state to persist
        """
        ...


@dataclass
class SagaStep:
    """A single step in a saga with action and compensation.

    Each step has:
    - An action that performs work
    - A compensation that rolls back the work if saga fails
    """

    name: str
    """Name of the step"""

    action: Callable[..., Any]
    """Async function to execute for this step"""

    compensation: Optional[Callable[..., Any]] = None
    """Async function to compensate (rollback) this step"""

    def __post_init__(self) -> None:
        """Validate step configuration."""
        if not self.name:
            raise ValueError("Step name cannot be empty")
        if not self.action:
            raise ValueError("Step action cannot be None")


class Saga:
    """Orchestrates a saga execution with steps and compensations.

    Sagas enable distributed transactions across multiple aggregates:

    1. Execute steps in order
    2. If a step fails, compensate all completed steps in reverse order
    3. Track state for recovery from failures
    4. Support async actions and compensations

    Usage:
        saga = Saga("TransferMoney", [
            SagaStep(
                name="debit",
                action=debit_account,
                compensation=credit_account
            ),
            SagaStep(
                name="credit",
                action=credit_account,
                compensation=debit_account
            )
        ])

        result = await saga.execute(from_account=..., to_account=..., amount=...)
    """

    def __init__(
        self,
        saga_type: str,
        steps: list[SagaStep],
        state_store: SagaStateStore,
        tracing: Optional[TracingProvider] = None,
    ):
        """Initialize a saga.

        Args:
            saga_type: Type of saga (for monitoring/debugging)
            steps: List of saga steps to execute
            state_store: Store for saga state persistence
            tracing: Optional tracing provider
        """
        self.saga_type = saga_type
        self.steps = steps
        self.state_store = state_store
        self.tracing = tracing
        self.saga_id = str(uuid.uuid4())
        self._state: Optional[SagaState] = None
        self._step_results: dict[str, Any] = {}

    async def initialize(self) -> None:
        """Load saga state from store or create new.

        Should be called once before execute().
        """
        self._state = await self.state_store.load_state(self.saga_id)
        if self._state is None:
            self._state = SagaState(saga_id=self.saga_id, saga_type=self.saga_type)
            await self.state_store.save_state(self._state)

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the saga with given parameters.

        Args:
            **kwargs: Arguments passed to each step action

        Returns:
            Result from the last step

        Raises:
            Exception: If any step fails and compensation also fails
        """
        if self._state is None:
            await self.initialize()

        # Update state
        object.__setattr__(self._state, "status", SagaStatus.IN_PROGRESS)
        object.__setattr__(
            self._state, "started_at", datetime.now(timezone.utc)
        )
        await self.state_store.save_state(self._state)

        try:
            # Execute steps in order
            for index, step in enumerate(self.steps):
                result = await self._execute_step(step, index, kwargs)
                self._step_results[step.name] = result

            # All steps completed
            object.__setattr__(self._state, "status", SagaStatus.COMPLETED)
            object.__setattr__(
                self._state, "completed_at", datetime.now(timezone.utc)
            )
            await self.state_store.save_state(self._state)

            return result

        except Exception as e:
            # Step failed - compensate
            await self._compensate(str(e))
            raise

    async def _execute_step(
        self, step: SagaStep, index: int, kwargs: dict[str, Any]
    ) -> Any:
        """Execute a single saga step.

        Args:
            step: The step to execute
            index: Index of this step in the saga
            kwargs: Arguments to pass to the step action

        Returns:
            Result from the action
        """
        # Update current step index
        object.__setattr__(self._state, "current_step_index", index)

        # Record step as starting
        step_status = SagaStepStatus(step_name=step.name)
        object.__setattr__(
            step_status, "started_at", datetime.now(timezone.utc)
        )
        step_statuses = dict(self._state.step_statuses)
        step_statuses[step.name] = step_status
        object.__setattr__(self._state, "step_statuses", step_statuses)

        try:
            # Execute the action
            result = await self._call_handler(step.action, kwargs)

            # Record step as completed
            object.__setattr__(step_status, "status", "completed")
            object.__setattr__(step_status, "result", result)
            object.__setattr__(
                step_status, "completed_at", datetime.now(timezone.utc)
            )
            await self.state_store.save_state(self._state)

            return result

        except Exception as e:
            # Record step as failed
            object.__setattr__(step_status, "status", "failed")
            object.__setattr__(step_status, "error", str(e))
            object.__setattr__(
                step_status, "completed_at", datetime.now(timezone.utc)
            )
            await self.state_store.save_state(self._state)
            raise

    async def _compensate(self, reason: str) -> None:
        """Compensate (rollback) completed steps in reverse order.

        Args:
            reason: Reason for compensation
        """
        object.__setattr__(self._state, "status", SagaStatus.COMPENSATING)
        object.__setattr__(self._state, "error", reason)
        await self.state_store.save_state(self._state)

        # Compensate in reverse order
        completed_indices = list(
            range(self._state.current_step_index + 1)
        )  # Inclusive

        for index in reversed(completed_indices):
            step = self.steps[index]

            if not step.compensation:
                # No compensation for this step
                continue

            step_statuses = dict(self._state.step_statuses)
            step_status = step_statuses.get(
                step.name, SagaStepStatus(step_name=step.name)
            )

            try:
                object.__setattr__(step_status, "status", "compensating")
                object.__setattr__(
                    step_status, "started_at", datetime.now(timezone.utc)
                )

                # Execute compensation with original action's result
                result = self._step_results.get(step.name)
                compensation_kwargs = {"result": result}
                compensation_kwargs.update(
                    {k: v for k, v in self._step_results.items() if k != step.name}
                )

                await self._call_handler(step.compensation, compensation_kwargs)

                object.__setattr__(step_status, "status", "compensated")
                object.__setattr__(
                    step_status, "completed_at", datetime.now(timezone.utc)
                )

            except Exception as e:
                # Compensation failed - saga is in failed state
                object.__setattr__(step_status, "status", "failed")
                object.__setattr__(step_status, "error", str(e))
                object.__setattr__(
                    step_status, "completed_at", datetime.now(timezone.utc)
                )
                object.__setattr__(self._state, "status", SagaStatus.FAILED)

            step_statuses[step.name] = step_status
            object.__setattr__(self._state, "step_statuses", step_statuses)

        # Final state
        if self._state.status == SagaStatus.COMPENSATING:
            object.__setattr__(self._state, "status", SagaStatus.FAILED)

        object.__setattr__(
            self._state, "completed_at", datetime.now(timezone.utc)
        )
        await self.state_store.save_state(self._state)

    async def _call_handler(
        self, handler: Callable[..., Any], kwargs: dict[str, Any]
    ) -> Any:
        """Call a handler function with proper async/sync handling.

        Args:
            handler: Function to call
            kwargs: Arguments to pass

        Returns:
            Result from handler
        """
        result = handler(**kwargs)
        if asyncio.iscoroutine(result):
            return await result  # type: ignore[misc]
        return result

    def get_state(self) -> Optional[SagaState]:
        """Get current saga state.

        Returns:
            The current state or None if not initialized
        """
        return self._state

    def is_completed(self) -> bool:
        """Check if saga execution is complete.

        Returns:
            True if saga is done (success or failure)
        """
        return self._state is not None and self._state.is_completed()

    def is_successful(self) -> bool:
        """Check if saga completed successfully.

        Returns:
            True if saga completed without errors
        """
        return (
            self._state is not None
            and self._state.status == SagaStatus.COMPLETED
        )


class InMemorySagaStateStore:
    """In-memory implementation of SagaStateStore for testing."""

    def __init__(self) -> None:
        self._states: dict[str, SagaState] = {}

    async def load_state(self, saga_id: str) -> Optional[SagaState]:
        """Load saga state.

        Args:
            saga_id: The saga identifier

        Returns:
            The saved state or None if not found
        """
        return self._states.get(saga_id)

    async def save_state(self, state: SagaState) -> None:
        """Save saga state.

        Args:
            state: The state to persist
        """
        self._states[state.saga_id] = state
