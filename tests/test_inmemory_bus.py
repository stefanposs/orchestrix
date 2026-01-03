"""Tests for InMemoryMessageBus."""

from orchestrix.message import Command, Event


class TestInMemoryMessageBus:
    """Tests for in-memory message bus implementation."""

    def test_publish_calls_single_handler(self, bus):
        """Test that publish calls a single registered handler."""
        called = []

        def handler(msg):
            called.append(msg)

        bus.subscribe(Command, handler)
        cmd = Command()
        bus.publish(cmd)

        assert len(called) == 1
        assert called[0] == cmd

    def test_publish_calls_multiple_handlers(self, bus):
        """Test that publish calls multiple handlers in order."""
        calls = []

        def handler1(msg):
            calls.append(("handler1", msg))

        def handler2(msg):
            calls.append(("handler2", msg))

        bus.subscribe(Command, handler1)
        bus.subscribe(Command, handler2)

        cmd = Command()
        bus.publish(cmd)

        assert len(calls) == 2
        assert calls[0][0] == "handler1"
        assert calls[1][0] == "handler2"
        assert calls[0][1] == cmd
        assert calls[1][1] == cmd

    def test_publish_only_calls_matching_type(self, bus):
        """Test that only handlers for the message type are called."""
        command_called = []
        event_called = []

        def command_handler(msg):
            command_called.append(msg)

        def event_handler(msg):
            event_called.append(msg)

        bus.subscribe(Command, command_handler)
        bus.subscribe(Event, event_handler)

        cmd = Command()
        bus.publish(cmd)

        assert len(command_called) == 1
        assert len(event_called) == 0

        evt = Event()
        bus.publish(evt)

        assert len(command_called) == 1
        assert len(event_called) == 1

    def test_publish_without_handlers(self, bus):
        """Test that publish works even without handlers."""
        cmd = Command()
        bus.publish(cmd)  # Should not raise

    def test_multiple_subscriptions_same_type(self, bus):
        """Test multiple handlers for the same message type."""
        calls = []

        bus.subscribe(Command, lambda msg: calls.append(1))
        bus.subscribe(Command, lambda msg: calls.append(2))
        bus.subscribe(Command, lambda msg: calls.append(3))

        bus.publish(Command())

        assert calls == [1, 2, 3]
