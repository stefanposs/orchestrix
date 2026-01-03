"""Tests for CloudEvents metadata fields."""

import pytest

from orchestrix.message import Command, Event, Message


class TestMessageMetadata:
    """Test CloudEvents metadata fields."""

    def test_message_with_all_metadata(self):
        """Test creating a message with all CloudEvents metadata."""

        class TestMessage(Message):
            pass

        msg = TestMessage(
            subject="users/123",
            datacontenttype="application/json",
            dataschema="https://example.com/schema/user",
            correlation_id="corr-123",
            causation_id="cause-456",
        )

        assert msg.subject == "users/123"
        assert msg.datacontenttype == "application/json"
        assert msg.dataschema == "https://example.com/schema/user"
        assert msg.correlation_id == "corr-123"
        assert msg.causation_id == "cause-456"

    def test_message_metadata_defaults_to_none(self):
        """Test that metadata fields default to None."""

        class TestMessage(Message):
            pass

        msg = TestMessage()

        assert msg.subject is None
        assert msg.datacontenttype is None
        assert msg.dataschema is None
        assert msg.correlation_id is None
        assert msg.causation_id is None

    def test_command_with_metadata(self):
        """Test Command with metadata fields."""

        class CreateUser(Command):
            username: str = "test"

        cmd = CreateUser(
            subject="users/create",
            correlation_id="req-789",
        )

        assert cmd.subject == "users/create"
        assert cmd.correlation_id == "req-789"
        assert cmd.username == "test"

    def test_event_with_causation_chain(self):
        """Test Event with causation tracking."""

        class UserCreated(Event):
            user_id: str = "user-123"

        # Command that causes the event
        command_id = "cmd-001"

        # Event caused by the command
        event = UserCreated(
            correlation_id="req-789",
            causation_id=command_id,
        )

        assert event.correlation_id == "req-789"
        assert event.causation_id == command_id
        assert event.user_id == "user-123"

    def test_metadata_immutability(self):
        """Test that metadata fields are immutable."""

        class TestMessage(Message):
            pass

        msg = TestMessage(correlation_id="test-123")

        with pytest.raises(Exception):  # FrozenInstanceError
            msg.correlation_id = "new-value"  # type: ignore[misc]

    def test_correlation_across_messages(self):
        """Test correlation ID flowing through message chain."""

        class OrderPlaced(Event):
            order_id: str = "ord-123"

        class ProcessPayment(Command):
            order_id: str = "ord-123"

        correlation_id = "flow-001"

        # Initial event
        event1 = OrderPlaced(correlation_id=correlation_id)

        # Command triggered by event (shares correlation_id, event is causation)
        cmd = ProcessPayment(
            correlation_id=event1.correlation_id,
            causation_id=event1.id,
        )

        # Resulting event
        class PaymentProcessed(Event):
            order_id: str = "ord-123"

        event2 = PaymentProcessed(
            correlation_id=cmd.correlation_id,
            causation_id=cmd.id,
        )

        # All share same correlation ID
        assert event1.correlation_id == correlation_id
        assert cmd.correlation_id == correlation_id
        assert event2.correlation_id == correlation_id

        # Causation chain is preserved
        assert cmd.causation_id == event1.id
        assert event2.causation_id == cmd.id
