"""Tests for Message, Command, and Event classes."""

from datetime import datetime

import pytest

from orchestrix.core.message import Command, Event, Message


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
