"""Tests for error handling in InMemoryMessageBus."""

import pytest
from orchestrix.core.common.exceptions import HandlerError
from orchestrix.core.messaging.message import Command
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus


@pytest.fixture
def bus():
    """Provide a fresh InMemoryMessageBus for each test."""
    return InMemoryMessageBus()


class MockCommand(Command):
    """Mock command for testing."""

    value: str = "test"


class TestErrorHandling:
    """Test error handling in message bus."""

    def test_handler_exception_does_not_stop_other_handlers(self, bus):
        """Test that one handler failing doesn't prevent others from running."""
        results = []

        def failing_handler(msg):
            raise ValueError("Handler failed")

        def success_handler(msg):
            results.append(msg.value)

        bus.subscribe(MockCommand, failing_handler)
        bus.subscribe(MockCommand, success_handler)

        # Should not raise - error is logged but doesn't stop execution
        bus.publish(MockCommand())

        # Success handler should have run
        assert len(results) == 1
        assert results[0] == "test"

    def test_all_handlers_fail_raises_error(self, bus):
        """Test that if all handlers fail, an error is raised."""

        def failing_handler_1(msg):
            raise ValueError("Handler 1 failed")

        def failing_handler_2(msg):
            raise RuntimeError("Handler 2 failed")

        bus.subscribe(MockCommand, failing_handler_1)
        bus.subscribe(MockCommand, failing_handler_2)

        with pytest.raises(HandlerError) as exc_info:
            bus.publish(MockCommand())

        assert "all_handlers" in str(exc_info.value)

    def test_no_handlers_does_not_raise(self, bus):
        """Test that publishing with no handlers doesn't raise."""
        # Should not raise
        bus.publish(MockCommand())

    def test_multiple_handlers_some_fail(self, bus):
        """Test mixed success and failure handlers."""
        results = []

        def handler1(msg):
            results.append("handler1")

        def handler2(msg):
            raise ValueError("Handler 2 failed")

        def handler3(msg):
            results.append("handler3")

        bus.subscribe(MockCommand, handler1)
        bus.subscribe(MockCommand, handler2)
        bus.subscribe(MockCommand, handler3)

        # Should not raise
        bus.publish(MockCommand())

        # Successful handlers should have run
        assert results == ["handler1", "handler3"]

    def test_handler_error_contains_context(self, bus):
        """Test that HandlerError contains useful context."""

        def failing_handler(msg):
            raise ValueError("Something went wrong")

        bus.subscribe(MockCommand, failing_handler)

        with pytest.raises(HandlerError) as exc_info:
            bus.publish(MockCommand())

        error = exc_info.value
        assert error.message_type == "MockCommand"
        assert error.handler_name == "all_handlers"
