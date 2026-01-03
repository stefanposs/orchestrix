"""Tests for dead letter queue."""

import pytest

from orchestrix.dead_letter_queue import (
    DeadLetteredMessage,
    InMemoryDeadLetterQueue,
)
from orchestrix.message import Command


class CreateOrder(Command):
    """Test command."""

    order_id: str = "order-001"


class TestInMemoryDeadLetterQueue:
    """Test in-memory dead letter queue."""

    @pytest.fixture
    def dlq(self) -> InMemoryDeadLetterQueue:
        """Provide a fresh dead letter queue."""
        return InMemoryDeadLetterQueue()

    def test_enqueue_message(self, dlq: InMemoryDeadLetterQueue) -> None:
        """Test enqueueing a message to DLQ."""
        cmd = CreateOrder()
        dead_lettered = DeadLetteredMessage(
            message=cmd,
            reason="Handler timeout",
            failure_count=3,
        )

        dlq.enqueue(dead_lettered)

        assert dlq.count() == 1

    def test_dequeue_all_messages(self, dlq: InMemoryDeadLetterQueue) -> None:
        """Test retrieving all messages from DLQ."""
        cmd1 = CreateOrder()
        cmd2 = CreateOrder()

        msg1 = DeadLetteredMessage(
            message=cmd1,
            reason="Timeout",
            failure_count=3,
        )
        msg2 = DeadLetteredMessage(
            message=cmd2,
            reason="Validation failed",
            failure_count=1,
        )

        dlq.enqueue(msg1)
        dlq.enqueue(msg2)

        all_messages = dlq.dequeue_all()

        assert len(all_messages) == 2
        assert all_messages[0].reason == "Timeout"
        assert all_messages[1].reason == "Validation failed"

    def test_clear_dlq(self, dlq: InMemoryDeadLetterQueue) -> None:
        """Test clearing all messages from DLQ."""
        cmd = CreateOrder()
        msg = DeadLetteredMessage(
            message=cmd,
            reason="Failed",
            failure_count=2,
        )

        dlq.enqueue(msg)
        assert dlq.count() == 1

        dlq.clear()

        assert dlq.count() == 0
        assert len(dlq.dequeue_all()) == 0

    def test_count_messages(self, dlq: InMemoryDeadLetterQueue) -> None:
        """Test counting messages in DLQ."""
        assert dlq.count() == 0

        for i in range(5):
            cmd = CreateOrder()
            msg = DeadLetteredMessage(
                message=cmd,
                reason=f"Error {i}",
                failure_count=i + 1,
            )
            dlq.enqueue(msg)

        assert dlq.count() == 5

    def test_get_by_message_id(self, dlq: InMemoryDeadLetterQueue) -> None:
        """Test retrieving a message by ID."""
        cmd1 = CreateOrder()
        cmd2 = CreateOrder()

        msg1 = DeadLetteredMessage(
            message=cmd1,
            reason="Error 1",
            failure_count=1,
        )
        msg2 = DeadLetteredMessage(
            message=cmd2,
            reason="Error 2",
            failure_count=2,
        )

        dlq.enqueue(msg1)
        dlq.enqueue(msg2)

        found = dlq.get_by_message_id(cmd1.id)

        assert found is not None
        assert found.message.id == cmd1.id
        assert found.reason == "Error 1"

    def test_get_by_message_id_not_found(
        self, dlq: InMemoryDeadLetterQueue
    ) -> None:
        """Test retrieving non-existent message ID."""
        not_found = dlq.get_by_message_id("nonexistent-id")

        assert not_found is None

    def test_get_by_reason(self, dlq: InMemoryDeadLetterQueue) -> None:
        """Test filtering messages by reason."""
        msg1 = DeadLetteredMessage(
            message=CreateOrder(),
            reason="Timeout",
            failure_count=3,
        )
        msg2 = DeadLetteredMessage(
            message=CreateOrder(),
            reason="Timeout",
            failure_count=3,
        )
        msg3 = DeadLetteredMessage(
            message=CreateOrder(),
            reason="Validation failed",
            failure_count=1,
        )

        dlq.enqueue(msg1)
        dlq.enqueue(msg2)
        dlq.enqueue(msg3)

        timeout_msgs = dlq.get_by_reason("Timeout")

        assert len(timeout_msgs) == 2
        assert all(msg.reason == "Timeout" for msg in timeout_msgs)

    def test_get_by_reason_none_found(
        self, dlq: InMemoryDeadLetterQueue
    ) -> None:
        """Test filtering by non-existent reason."""
        dlq.enqueue(
            DeadLetteredMessage(
                message=CreateOrder(),
                reason="Error",
                failure_count=1,
            )
        )

        result = dlq.get_by_reason("Nonexistent")

        assert len(result) == 0

    def test_dead_lettered_message_immutable(self) -> None:
        """Test that DeadLetteredMessage is immutable."""
        cmd = CreateOrder()
        msg = DeadLetteredMessage(
            message=cmd,
            reason="Error",
            failure_count=1,
        )

        with pytest.raises(AttributeError):
            msg.reason = "New reason"  # type: ignore

    def test_dequeue_returns_copy(self, dlq: InMemoryDeadLetterQueue) -> None:
        """Test that dequeue_all returns a copy (can modify without affecting DLQ)."""
        msg = DeadLetteredMessage(
            message=CreateOrder(),
            reason="Error",
            failure_count=1,
        )
        dlq.enqueue(msg)

        messages = dlq.dequeue_all()
        original_count = dlq.count()

        # Modify the returned list
        messages.clear()

        # DLQ should still have the message
        assert dlq.count() == original_count
        assert len(dlq.dequeue_all()) == 1

    def test_dead_lettered_message_preserves_metadata(self) -> None:
        """Test that DeadLetteredMessage preserves original message metadata."""
        cmd = CreateOrder()
        reason = "Handler threw exception"
        failure_count = 5

        msg = DeadLetteredMessage(
            message=cmd,
            reason=reason,
            failure_count=failure_count,
        )

        assert msg.message.id == cmd.id
        assert msg.message.type == cmd.type
        assert msg.reason == reason
        assert msg.failure_count == failure_count
        assert msg.timestamp is not None
