"""Tests for structured logging module.

Tests logger creation, structured logging, and context formatting.
"""

import logging
from io import StringIO
from unittest.mock import MagicMock

from orchestrix.core.common.logging import StructuredLogger, get_logger


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_basic(self) -> None:
        """Test getting logger with simple name."""
        logger = get_logger("test_module")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert "orchestrix.test_module" in logger.name

    def test_get_logger_nested_module(self) -> None:
        """Test getting logger for nested module."""
        logger = get_logger("core.eventsourcing.aggregate")

        assert logger is not None
        assert "orchestrix.core.eventsourcing.aggregate" in logger.name

    def test_get_logger_caches(self) -> None:
        """Test that get_logger returns same instance."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")

        assert logger1 is logger2

    def test_get_logger_names_differ(self) -> None:
        """Test that different names return different loggers."""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")

        assert logger1 is not logger2
        assert "orchestrix.test1" in logger1.name
        assert "orchestrix.test2" in logger2.name


class TestStructuredLogger:
    """Tests for StructuredLogger class."""

    def test_creation(self) -> None:
        """Test creating structured logger."""
        base_logger = logging.getLogger("test")
        logger = StructuredLogger(base_logger)

        assert logger.logger is base_logger

    def test_format_context_empty(self) -> None:
        """Test formatting empty context."""
        base_logger = logging.getLogger("test")
        logger = StructuredLogger(base_logger)

        result = logger._format_context()

        assert result == ""

    def test_format_context_single_item(self) -> None:
        """Test formatting context with single item."""
        base_logger = logging.getLogger("test")
        logger = StructuredLogger(base_logger)

        result = logger._format_context(user_id="123")

        assert result == " [user_id=123]"

    def test_format_context_multiple_items(self) -> None:
        """Test formatting context with multiple items."""
        base_logger = logging.getLogger("test")
        logger = StructuredLogger(base_logger)

        result = logger._format_context(
            user_id="123", action="login", timestamp="2024-01-03T10:00:00"
        )

        # Check all items are present (order may vary)
        assert "user_id=123" in result
        assert "action=login" in result
        assert "timestamp=2024-01-03T10:00:00" in result
        assert result.startswith(" [")
        assert result.endswith("]")

    def test_format_context_various_types(self) -> None:
        """Test formatting context with various data types."""
        base_logger = logging.getLogger("test")
        logger = StructuredLogger(base_logger)

        result = logger._format_context(
            string_val="test", int_val=42, float_val=3.14, bool_val=True, none_val=None
        )

        assert "string_val=test" in result
        assert "int_val=42" in result
        assert "float_val=3.14" in result
        assert "bool_val=True" in result
        assert "none_val=None" in result

    def test_info_logging(self) -> None:
        """Test info level logging."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        logger.info("User logged in", user_id="123")

        base_logger.info.assert_called_once()
        call_args = base_logger.info.call_args[0][0]
        assert "User logged in" in call_args
        assert "user_id=123" in call_args

    def test_info_logging_no_context(self) -> None:
        """Test info logging without context."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        logger.info("Simple message")

        base_logger.info.assert_called_once_with("Simple message")

    def test_error_logging(self) -> None:
        """Test error level logging."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        logger.error("Database connection failed", retry_count=3)

        base_logger.error.assert_called_once()
        call_args = base_logger.error.call_args[0][0]
        assert "Database connection failed" in call_args
        assert "retry_count=3" in call_args

    def test_warning_logging(self) -> None:
        """Test warning level logging."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        logger.warning("Slow query detected", duration_ms=5000)

        base_logger.warning.assert_called_once()
        call_args = base_logger.warning.call_args[0][0]
        assert "Slow query detected" in call_args
        assert "duration_ms=5000" in call_args

    def test_debug_logging(self) -> None:
        """Test debug level logging."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        logger.debug("Processing aggregate", aggregate_id="agg-123")

        base_logger.debug.assert_called_once()
        call_args = base_logger.debug.call_args[0][0]
        assert "Processing aggregate" in call_args
        assert "aggregate_id=agg-123" in call_args

    def test_multiple_context_fields(self) -> None:
        """Test logging with multiple context fields."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        logger.info(
            "Event processed",
            event_type="UserCreated",
            aggregate_id="user-1",
            version=1,
            timestamp="2024-01-03T10:00:00",
        )

        base_logger.info.assert_called_once()
        call_args = base_logger.info.call_args[0][0]
        assert "Event processed" in call_args
        assert "event_type=UserCreated" in call_args
        assert "aggregate_id=user-1" in call_args
        assert "version=1" in call_args
        assert "timestamp=2024-01-03T10:00:00" in call_args


class TestStructuredLoggerIntegration:
    """Integration tests for structured logger."""

    def test_real_logging_output(self) -> None:
        """Test actual logging output with real handler."""
        # Create logger with string handler
        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        base_logger = logging.getLogger("test_integration")
        base_logger.handlers.clear()  # Remove existing handlers
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.DEBUG)

        logger = StructuredLogger(base_logger)

        # Log with context
        logger.info("Test message", key="value")

        # Get output
        output = handler.stream.getvalue()
        assert "Test message" in output
        assert "key=value" in output

    def test_structured_logger_preserves_log_level(self) -> None:
        """Test that log level is respected."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        # These should all be called regardless of level
        logger.info("info")
        logger.warning("warning")
        logger.error("error")
        logger.debug("debug")

        assert base_logger.info.called
        assert base_logger.warning.called
        assert base_logger.error.called
        assert base_logger.debug.called

    def test_complex_context_scenario(self) -> None:
        """Test realistic logging scenario with complex context."""
        base_logger = MagicMock(spec=logging.Logger)
        logger = StructuredLogger(base_logger)

        # Simulate event sourcing operation
        aggregate_id = "bank-account-1"
        event_type = "MoneyTransferred"
        amount = 100.50
        from_account = "account-1"
        to_account = "account-2"

        logger.info(
            "Event stored successfully",
            aggregate_id=aggregate_id,
            event_type=event_type,
            amount=amount,
            from_account=from_account,
            to_account=to_account,
            sequence=1,
        )

        base_logger.info.assert_called_once()
        call_args = base_logger.info.call_args[0][0]

        assert aggregate_id in call_args
        assert event_type in call_args
        assert str(amount) in call_args
        assert str(1) in call_args  # sequence
