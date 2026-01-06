"""Logging configuration for Orchestrix.

Provides structured logging with message context.
"""

import logging

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"orchestrix.{name}")


class StructuredLogger:
    """Logger wrapper that adds structured context to log messages."""

    def __init__(self, logger: logging.Logger):
        """Initialize with a logger instance.

        Args:
            logger: Base logger to wrap
        """
        self.logger = logger

    def _format_context(self, **context: str | int | float | bool | None) -> str:
        """Format context dictionary as key=value pairs.

        Args:
            **context: Context key-value pairs

        Returns:
            Formatted context string
        """
        if not context:
            return ""
        items = [f"{k}={v}" for k, v in context.items()]
        return f" [{', '.join(items)}]"

    def info(self, message: str, **context: str | int | float | bool | None) -> None:
        """Log info message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        self.logger.info(f"{message}{self._format_context(**context)}")

    def error(self, message: str, **context: str | int | float | bool | None) -> None:
        """Log error message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        self.logger.error(f"{message}{self._format_context(**context)}")

    def exception(self, message: str, **context: str | int | float | bool | None) -> None:
        """Log exception message with context and traceback.

        Args:
            message: Log message
            **context: Additional context fields
        """
        self.logger.exception(f"{message}{self._format_context(**context)}")

    def warning(self, message: str, **context: str | int | float | bool | None) -> None:
        """Log warning message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        self.logger.warning(f"{message}{self._format_context(**context)}")

    def debug(self, message: str, **context: str | int | float | bool | None) -> None:
        """Log debug message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        self.logger.debug(f"{message}{self._format_context(**context)}")
