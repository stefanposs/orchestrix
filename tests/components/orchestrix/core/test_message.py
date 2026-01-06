"""Tests for Message, Command, and Event classes."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from orchestrix.core.messaging.message import Command, Event, Message


class TestMessage:
    """Tests for Message base class."""

    def test_message_creation_with_defaults(self):
        """Test that Message creates with default values."""
        msg = Message()

        assert msg.id != ""
        assert msg.type == "Message"
        assert msg.source == "orchestrix"
        assert isinstance(msg.timestamp, datetime)

    def test_message_immutability(self):
        """Test that Message is immutable."""
        msg = Message()

        with pytest.raises(Exception):  # Frozen dataclass raises error
            msg.id = "new-id"  # type: ignore[misc]

    def test_message_type_from_class_name(self):
        """Test that type is set from class name."""

        class CustomMessage(Message):
            pass

        msg = CustomMessage()
        assert msg.type == "CustomMessage"

    def test_message_id_is_valid_uuid(self):
        """Test that message ID is valid UUID format."""
        msg = Message()
        # Should be able to parse as UUID
        uuid_obj = UUID(msg.id)
        assert str(uuid_obj) == msg.id

    def test_message_id_is_unique(self):
        """Test that each message gets unique ID."""
        msg1 = Message()
        msg2 = Message()
        assert msg1.id != msg2.id

    def test_message_with_custom_fields(self):
        """Test creating message with custom fields."""
        now = datetime.now(UTC)
        msg = Message(
            id="msg-123",
            type="CustomMessage",
            source="test-service",
            timestamp=now,
            subject="test-subject",
            datacontenttype="application/json",
            dataschema="https://example.com/schema",
            correlation_id="corr-123",
            causation_id="cause-456",
        )

        assert msg.id == "msg-123"
        assert msg.type == "CustomMessage"
        assert msg.source == "test-service"
        assert msg.timestamp == now
        assert msg.subject == "test-subject"
        assert msg.datacontenttype == "application/json"
        assert msg.dataschema == "https://example.com/schema"
        assert msg.correlation_id == "corr-123"
        assert msg.causation_id == "cause-456"

    def test_message_optional_fields_default_to_none(self):
        """Test that optional fields default to None."""
        msg = Message()

        assert msg.subject is None
        assert msg.datacontenttype is None
        assert msg.dataschema is None
        assert msg.correlation_id is None
        assert msg.causation_id is None

    def test_message_timestamp_is_current(self):
        """Test that timestamp is approximately now."""
        before = datetime.now(UTC)
        msg = Message()
        after = datetime.now(UTC)

        assert before <= msg.timestamp <= after

    def test_message_type_with_no_explicit_value(self):
        """Test type defaults to class name when not provided."""
        msg = Message()
        assert msg.type == "Message"

    def test_message_type_can_be_overridden(self):
        """Test that type can be explicitly set."""
        msg = Message(type="CustomType")
        assert msg.type == "CustomType"


class TestCommand:
    """Tests for Command class."""

    def test_command_inherits_from_message(self):
        """Test that Command inherits from Message."""
        cmd = Command()

        assert isinstance(cmd, Message)
        assert cmd.type == "Command"

    def test_command_immutability(self):
        """Test that Command is immutable."""
        cmd = Command()

        with pytest.raises(Exception):
            cmd.id = "new-id"  # type: ignore[misc]

    def test_command_with_custom_type(self):
        """Test command with custom type."""
        cmd = Command(type="CreateUser")
        assert cmd.type == "CreateUser"

    def test_command_subclass_type(self):
        """Test that command subclass has correct type."""

        class CreateUserCommand(Command):
            pass

        cmd = CreateUserCommand()
        assert cmd.type == "CreateUserCommand"

    def test_command_with_causation_tracking(self):
        """Test command with causation ID for tracing."""
        parent_cmd = Command(type="InitiatePay")
        follow_up = Command(
            type="ConfirmPay", causation_id=parent_cmd.id, correlation_id=parent_cmd.id
        )

        assert follow_up.causation_id == parent_cmd.id
        assert follow_up.correlation_id == parent_cmd.id

    def test_command_timestamp(self):
        """Test command has timestamp."""
        cmd = Command()
        assert isinstance(cmd.timestamp, datetime)

    def test_command_with_all_fields(self):
        """Test command with all message fields set."""
        now = datetime.now(UTC)
        cmd = Command(
            id="cmd-1",
            type="TransferMoney",
            source="payment-service",
            timestamp=now,
            subject="transfer-001",
            datacontenttype="application/json",
            correlation_id="corr-123",
        )

        assert cmd.id == "cmd-1"
        assert cmd.type == "TransferMoney"
        assert cmd.source == "payment-service"
        assert cmd.subject == "transfer-001"
        assert cmd.correlation_id == "corr-123"


class TestEvent:
    """Tests for Event class."""

    def test_event_inherits_from_message(self):
        """Test that Event inherits from Message."""
        evt = Event()

        assert isinstance(evt, Message)
        assert evt.type == "Event"

    def test_event_immutability(self):
        """Test that Event is immutable."""
        evt = Event()

        with pytest.raises(Exception):
            evt.id = "new-id"  # type: ignore[misc]

    def test_event_with_custom_type(self):
        """Test event with custom type."""
        evt = Event(type="UserCreated")
        assert evt.type == "UserCreated"

    def test_event_subclass_type(self):
        """Test that event subclass has correct type."""

        class UserCreatedEvent(Event):
            pass

        evt = UserCreatedEvent()
        assert evt.type == "UserCreatedEvent"

    def test_event_with_causation_tracking(self):
        """Test event with causation ID from command."""
        cmd = Command(type="CreateUser")
        evt = Event(type="UserCreated", causation_id=cmd.id, correlation_id=cmd.id)

        assert evt.causation_id == cmd.id
        assert evt.correlation_id == cmd.id
        assert isinstance(evt, Message)

    def test_event_timestamp(self):
        """Test event has timestamp."""
        evt = Event()
        assert isinstance(evt.timestamp, datetime)

    def test_event_with_all_fields(self):
        """Test event with all message fields set."""
        now = datetime.now(UTC)
        evt = Event(
            id="evt-1",
            type="MoneyTransferred",
            source="bank-service",
            timestamp=now,
            subject="transfer-001",
            dataschema="https://example.com/schemas/transfer.json",
            correlation_id="corr-789",
        )

        assert evt.id == "evt-1"
        assert evt.type == "MoneyTransferred"
        assert evt.source == "bank-service"
        assert evt.subject == "transfer-001"
        assert evt.dataschema == "https://example.com/schemas/transfer.json"
        assert evt.correlation_id == "corr-789"


class TestCloudEventsCompliance:
    """Tests for CloudEvents v1.0 specification compliance."""

    def test_event_required_attributes(self):
        """Test CloudEvents required attributes are present."""
        evt = Event()

        assert evt.id is not None
        assert evt.type is not None
        assert evt.source is not None
        assert evt.timestamp is not None

    def test_event_optional_attributes(self):
        """Test CloudEvents optional attributes."""
        evt = Event(
            subject="subject-123",
            datacontenttype="application/json",
            dataschema="https://example.com/schema",
        )

        assert evt.subject == "subject-123"
        assert evt.datacontenttype == "application/json"
        assert evt.dataschema == "https://example.com/schema"

    def test_event_extension_attributes(self):
        """Test CloudEvents extension attributes (correlation, causation)."""
        evt = Event(correlation_id="corr-123", causation_id="cause-456")

        assert evt.correlation_id == "corr-123"
        assert evt.causation_id == "cause-456"

    def test_timestamp_iso_8601_compatible(self):
        """Test timestamp is ISO 8601 compatible."""
        evt = Event()
        iso_format = evt.timestamp.isoformat()

        # Should have ISO 8601 components
        assert "T" in iso_format  # Date/time separator
        assert "+" in iso_format or "-" in iso_format  # Timezone offset


class TestMessageCausationChain:
    """Tests for causation/correlation ID chaining."""

    def test_correlation_chain(self):
        """Test events with same correlation ID form a chain."""
        root_correlation = "corr-123"

        cmd = Command(correlation_id=root_correlation)
        evt = Event(causation_id=cmd.id, correlation_id=root_correlation)
        follow_up_cmd = Command(causation_id=evt.id, correlation_id=root_correlation)

        # All should have same correlation
        assert cmd.correlation_id == root_correlation
        assert evt.correlation_id == root_correlation
        assert follow_up_cmd.correlation_id == root_correlation

        # Causation should be chained
        assert evt.causation_id == cmd.id
        assert follow_up_cmd.causation_id == evt.id

    def test_separate_causation_chains_different(self):
        """Test different chains don't share correlation IDs."""
        chain1 = Event(correlation_id="chain1-123")
        chain2 = Event(correlation_id="chain2-456")

        assert chain1.correlation_id != chain2.correlation_id
