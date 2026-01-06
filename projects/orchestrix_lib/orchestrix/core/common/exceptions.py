"""Exception types for Orchestrix."""


class OrchestrixError(Exception):
    """Base exception for all Orchestrix errors."""


class HandlerError(OrchestrixError):
    """Exception raised when a message handler fails."""

    def __init__(self, message_type: str, handler_name: str, original_error: Exception):
        """Initialize handler error.

        Args:
            message_type: The type of message being handled
            handler_name: The name of the handler that failed
            original_error: The original exception
        """
        self.message_type = message_type
        self.handler_name = handler_name
        self.original_error = original_error
        super().__init__(
            f"Handler '{handler_name}' failed for message type '{message_type}': {original_error}"
        )


class ConcurrencyError(OrchestrixError):
    """Exception raised when optimistic locking detects a version conflict.

    This occurs when trying to save events for an aggregate that has been
    modified by another process since it was loaded.
    """

    def __init__(self, aggregate_id: str, expected_version: int, actual_version: int):
        """Initialize concurrency error.

        Args:
            aggregate_id: The aggregate that had the conflict
            expected_version: The version we expected
            actual_version: The actual current version
        """
        self.aggregate_id = aggregate_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Concurrency conflict for aggregate '{aggregate_id}': "
            f"expected version {expected_version}, but current version is {actual_version}"
        )
