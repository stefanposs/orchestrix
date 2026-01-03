"""Tests for saga orchestration framework."""

import asyncio
from typing import Any

import pytest

from orchestrix.core.saga import (
    InMemorySagaStateStore,
    Saga,
    SagaState,
    SagaStatus,
    SagaStep,
)


class TestSagaStep:
    """Tests for SagaStep."""

    def test_valid_step(self):
        """Test creating a valid saga step."""

        async def action() -> None:
            pass

        async def compensation() -> None:
            pass

        step = SagaStep(
            name="test-step", action=action, compensation=compensation
        )
        assert step.name == "test-step"
        assert step.action == action
        assert step.compensation == compensation

    def test_step_without_compensation(self):
        """Test creating a step without compensation."""

        async def action() -> None:
            pass

        step = SagaStep(name="test-step", action=action)
        assert step.name == "test-step"
        assert step.action == action
        assert step.compensation is None

    def test_step_requires_name(self):
        """Test that step requires a name."""

        async def action() -> None:
            pass

        with pytest.raises(ValueError, match="Step name cannot be empty"):
            SagaStep(name="", action=action)

    def test_step_requires_action(self):
        """Test that step requires an action."""

        async def compensation() -> None:
            pass

        with pytest.raises(ValueError, match="Step action cannot be None"):
            SagaStep(name="test", action=None, compensation=compensation)  # type: ignore


class TestSaga:
    """Tests for saga orchestration."""

    @pytest.fixture
    def state_store(self):
        """Create an in-memory state store."""
        return InMemorySagaStateStore()

    @pytest.fixture
    def saga(self, state_store):
        """Create a test saga."""
        steps = [
            SagaStep(name="step1", action=self._action_step1),
            SagaStep(name="step2", action=self._action_step2),
        ]
        return Saga("test-saga", steps, state_store)

    async def _action_step1(self, **kwargs: Any) -> str:
        """Test action for step 1."""
        return "result1"

    async def _action_step2(self, **kwargs: Any) -> str:
        """Test action for step 2."""
        return "result2"

    @pytest.mark.asyncio
    async def test_initialization(self, saga, state_store):
        """Test saga initialization."""
        await saga.initialize()

        state = saga.get_state()
        assert state is not None
        assert state.saga_type == "test-saga"
        assert state.status == SagaStatus.PENDING
        assert state.current_step_index == 0

    @pytest.mark.asyncio
    async def test_successful_execution(self, saga, state_store):
        """Test successful saga execution."""
        await saga.initialize()

        result = await saga.execute()

        assert result == "result2"
        assert saga.is_successful()

        state = saga.get_state()
        assert state is not None
        assert state.status == SagaStatus.COMPLETED
        assert len(state.step_statuses) == 2
        assert state.step_statuses["step1"].status == "completed"
        assert state.step_statuses["step2"].status == "completed"

    @pytest.mark.asyncio
    async def test_failed_step(self, state_store):
        """Test saga execution with failing step."""

        async def failing_action(**kwargs: Any) -> None:
            raise ValueError("Step failed")

        saga = Saga(
            "failing-saga",
            [SagaStep(name="fail-step", action=failing_action)],
            state_store,
        )
        await saga.initialize()

        with pytest.raises(ValueError, match="Step failed"):
            await saga.execute()

        state = saga.get_state()
        assert state is not None
        assert state.status == SagaStatus.FAILED
        assert state.step_statuses["fail-step"].status == "failed"

    @pytest.mark.asyncio
    async def test_compensation_on_failure(self, state_store):
        """Test compensation is called on failure."""
        compensation_called = []

        async def action1(**kwargs: Any) -> str:
            return "result1"

        async def compensation1(result: str, **kwargs: Any) -> None:
            compensation_called.append("comp1")

        async def action2(**kwargs: Any) -> None:
            raise ValueError("Step 2 failed")

        saga = Saga(
            "compensation-saga",
            [
                SagaStep(
                    name="step1", action=action1, compensation=compensation1
                ),
                SagaStep(name="step2", action=action2),
            ],
            state_store,
        )
        await saga.initialize()

        with pytest.raises(ValueError):
            await saga.execute()

        # Compensation should have been called
        assert "comp1" in compensation_called
        state = saga.get_state()
        assert state is not None
        assert state.status == SagaStatus.FAILED

    @pytest.mark.asyncio
    async def test_compensation_order(self, state_store):
        """Test compensations are called in reverse order."""
        compensation_order = []

        async def action1(**kwargs: Any) -> str:
            return "r1"

        async def action2(**kwargs: Any) -> str:
            return "r2"

        async def action3(**kwargs: Any) -> None:
            raise ValueError("Fail")

        async def comp1(result: str, **kwargs: Any) -> None:
            compensation_order.append(1)

        async def comp2(result: str, **kwargs: Any) -> None:
            compensation_order.append(2)

        saga = Saga(
            "order-saga",
            [
                SagaStep(name="step1", action=action1, compensation=comp1),
                SagaStep(name="step2", action=action2, compensation=comp2),
                SagaStep(name="step3", action=action3),
            ],
            state_store,
        )
        await saga.initialize()

        with pytest.raises(ValueError):
            await saga.execute()

        # Should be in reverse order: 2, 1
        assert compensation_order == [2, 1]

    @pytest.mark.asyncio
    async def test_step_with_arguments(self, state_store):
        """Test passing arguments to saga steps."""
        results = []

        async def action_with_args(value: int, **kwargs: Any) -> int:
            results.append(value)
            return value * 2

        saga = Saga(
            "args-saga",
            [SagaStep(name="step1", action=action_with_args)],
            state_store,
        )
        await saga.initialize()

        result = await saga.execute(value=10)

        assert result == 20
        assert results == [10]

    @pytest.mark.asyncio
    async def test_sync_handlers(self, state_store):
        """Test saga with sync handlers."""

        def sync_action(**kwargs: Any) -> str:
            return "sync-result"

        def sync_compensation(result: str, **kwargs: Any) -> None:
            pass

        saga = Saga(
            "sync-saga",
            [
                SagaStep(
                    name="sync-step",
                    action=sync_action,
                    compensation=sync_compensation,
                )
            ],
            state_store,
        )
        await saga.initialize()

        result = await saga.execute()

        assert result == "sync-result"
        assert saga.is_successful()

    @pytest.mark.asyncio
    async def test_state_persistence(self, state_store):
        """Test saga state is persisted."""
        steps = [
            SagaStep(
                name="step1",
                action=async_action_helper,
            ),
        ]
        saga = Saga("persist-saga", steps, state_store)
        saga_id = saga.saga_id

        await saga.initialize()
        await saga.execute()

        # Load saga from store
        saved_state = await state_store.load_state(saga_id)
        assert saved_state is not None
        assert saved_state.saga_type == "persist-saga"
        assert saved_state.status == SagaStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_saga_recovery(self, state_store):
        """Test recovering saga from persisted state."""
        steps = [
            SagaStep(
                name="step1",
                action=async_action_helper,
            ),
        ]
        saga1 = Saga("recover-saga", steps, state_store)
        saga_id = saga1.saga_id

        await saga1.initialize()
        state_before = saga1.get_state()
        assert state_before is not None

        # Load same saga by ID
        saga2 = Saga("recover-saga", steps, state_store)
        saga2.saga_id = saga_id
        await saga2.initialize()

        state_after = saga2.get_state()
        assert state_after is not None
        assert state_after.saga_id == saga_id

    @pytest.mark.asyncio
    async def test_is_completed(self, state_store):
        """Test is_completed status."""

        async def action(**kwargs: Any) -> None:
            pass

        saga = Saga("status-saga", [SagaStep(name="step", action=action)], state_store)

        assert not saga.is_completed()

        await saga.initialize()
        assert not saga.is_completed()

        await saga.execute()
        assert saga.is_completed()

    @pytest.mark.asyncio
    async def test_is_successful(self, state_store):
        """Test is_successful status."""

        async def action(**kwargs: Any) -> None:
            pass

        async def failing_action(**kwargs: Any) -> None:
            raise ValueError("Fail")

        # Successful saga
        saga1 = Saga(
            "success-saga", [SagaStep(name="step", action=action)], state_store
        )
        await saga1.initialize()
        await saga1.execute()
        assert saga1.is_successful()

        # Failed saga
        saga2 = Saga(
            "fail-saga",
            [SagaStep(name="step", action=failing_action)],
            state_store,
        )
        await saga2.initialize()
        try:
            await saga2.execute()
        except ValueError:
            pass
        assert not saga2.is_successful()

    @pytest.mark.asyncio
    async def test_compensation_with_failed_compensation(self, state_store):
        """Test saga failure when compensation fails."""

        async def action1(**kwargs: Any) -> str:
            return "r1"

        async def failing_compensation(result: str, **kwargs: Any) -> None:
            raise ValueError("Compensation failed")

        async def action2(**kwargs: Any) -> None:
            raise ValueError("Step failed")

        saga = Saga(
            "bad-comp-saga",
            [
                SagaStep(
                    name="step1",
                    action=action1,
                    compensation=failing_compensation,
                ),
                SagaStep(name="step2", action=action2),
            ],
            state_store,
        )
        await saga.initialize()

        with pytest.raises(ValueError):
            await saga.execute()

        state = saga.get_state()
        assert state is not None
        assert state.status == SagaStatus.FAILED

    @pytest.mark.asyncio
    async def test_multiple_sagas(self, state_store):
        """Test multiple independent sagas."""

        async def action(**kwargs: Any) -> str:
            return "result"

        saga1 = Saga(
            "saga1", [SagaStep(name="step", action=action)], state_store
        )
        saga2 = Saga(
            "saga2", [SagaStep(name="step", action=action)], state_store
        )

        saga1_id = saga1.saga_id
        saga2_id = saga2.saga_id

        await saga1.initialize()
        await saga2.initialize()

        await saga1.execute()
        await saga2.execute()

        # Both should be completed independently
        state1 = await state_store.load_state(saga1_id)
        state2 = await state_store.load_state(saga2_id)

        assert state1 is not None
        assert state2 is not None
        assert state1.status == SagaStatus.COMPLETED
        assert state2.status == SagaStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_concurrent_saga_steps(self, state_store):
        """Test saga execution doesn't run steps concurrently."""
        execution_order = []

        async def action1(**kwargs: Any) -> None:
            execution_order.append("start1")
            await asyncio.sleep(0.01)
            execution_order.append("end1")

        async def action2(**kwargs: Any) -> None:
            execution_order.append("start2")
            await asyncio.sleep(0.01)
            execution_order.append("end2")

        saga = Saga(
            "order-saga",
            [
                SagaStep(name="step1", action=action1),
                SagaStep(name="step2", action=action2),
            ],
            state_store,
        )
        await saga.initialize()
        await saga.execute()

        # Steps should execute sequentially
        assert execution_order == ["start1", "end1", "start2", "end2"]

    @pytest.mark.asyncio
    async def test_step_results_in_compensation(self, state_store):
        """Test that step results are passed to compensations."""
        compensated_results = []

        async def action1(**kwargs: Any) -> dict[str, str]:
            return {"id": "item-1", "value": "100"}

        async def action2(**kwargs: Any) -> dict[str, str]:
            return {"id": "item-2", "value": "200"}

        async def comp1(result: dict[str, str], **kwargs: Any) -> None:
            compensated_results.append(result)

        saga = Saga(
            "result-saga",
            [
                SagaStep(name="step1", action=action1, compensation=comp1),
                SagaStep(
                    name="step2",
                    action=lambda **kw: (_ for _ in ()).throw(ValueError("Fail")),
                ),
            ],
            state_store,
        )
        await saga.initialize()

        with pytest.raises(ValueError):
            await saga.execute()

        # Compensation should receive step1's result
        assert len(compensated_results) == 1
        assert compensated_results[0]["id"] == "item-1"


class TestInMemorySagaStateStore:
    """Tests for InMemorySagaStateStore."""

    def test_initialization(self):
        """Test state store initialization."""
        store = InMemorySagaStateStore()
        assert store is not None

    @pytest.mark.asyncio
    async def test_save_and_load(self):
        """Test saving and loading saga state."""
        store = InMemorySagaStateStore()

        state = SagaState(saga_id="test-saga", saga_type="test")
        await store.save_state(state)

        loaded_state = await store.load_state("test-saga")
        assert loaded_state is not None
        assert loaded_state.saga_id == "test-saga"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self):
        """Test loading nonexistent state returns None."""
        store = InMemorySagaStateStore()
        loaded_state = await store.load_state("nonexistent")
        assert loaded_state is None

    @pytest.mark.asyncio
    async def test_update_state(self):
        """Test updating existing state."""
        store = InMemorySagaStateStore()

        state1 = SagaState(saga_id="test-saga", saga_type="test")
        await store.save_state(state1)

        state2 = SagaState(
            saga_id="test-saga", saga_type="test", status=SagaStatus.COMPLETED
        )
        await store.save_state(state2)

        loaded_state = await store.load_state("test-saga")
        assert loaded_state is not None
        assert loaded_state.status == SagaStatus.COMPLETED


async def async_action_helper(**kwargs: Any) -> str:
    """Helper async action for tests."""
    return "result"
