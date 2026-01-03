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
