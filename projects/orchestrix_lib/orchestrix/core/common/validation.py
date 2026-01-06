"""Native validation utilities for messages.

Pure Python validation without external dependencies.
"""

from collections.abc import Sequence


class ValidationError(Exception):
    """Raised when message validation fails.

    Attributes:
        message: The validation error message
        field: The field that failed validation (optional)
        value: The invalid value (optional)
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: object = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message describing the validation failure
            field: Name of the field that failed validation
            value: The invalid value that was provided
        """
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value

    def __str__(self) -> str:
        """Format error message."""
        if self.field:
            return f"Validation failed for '{self.field}': {self.message}"
        return self.message


def validate_not_empty(value: str, field: str) -> None:
    """Validate that a string is not empty.

    Args:
        value: The string value to validate
        field: The field name for error messages

    Raises:
        ValidationError: If the string is empty or whitespace-only
    """
    if not value or not value.strip():
        msg = f"{field} cannot be empty"
        raise ValidationError(msg, field=field, value=value)


def validate_positive(value: float | int, field: str) -> None:
    """Validate that a number is positive.

    Args:
        value: The numeric value to validate
        field: The field name for error messages

    Raises:
        ValidationError: If the value is not positive
    """
    if value <= 0:
        msg = f"{field} must be positive"
        raise ValidationError(msg, field=field, value=value)


def validate_non_negative(value: float | int, field: str) -> None:
    """Validate that a number is non-negative.

    Args:
        value: The numeric value to validate
        field: The field name for error messages

    Raises:
        ValidationError: If the value is negative
    """
    if value < 0:
        msg = f"{field} cannot be negative"
        raise ValidationError(msg, field=field, value=value)


def validate_min_length(value: str, min_length: int, field: str) -> None:
    """Validate minimum string length.

    Args:
        value: The string value to validate
        min_length: Minimum required length
        field: The field name for error messages

    Raises:
        ValidationError: If the string is too short
    """
    if len(value) < min_length:
        msg = f"{field} must be at least {min_length} characters"
        raise ValidationError(msg, field=field, value=value)


def validate_max_length(value: str, max_length: int, field: str) -> None:
    """Validate maximum string length.

    Args:
        value: The string value to validate
        max_length: Maximum allowed length
        field: The field name for error messages

    Raises:
        ValidationError: If the string is too long
    """
    if len(value) > max_length:
        msg = f"{field} must be at most {max_length} characters"
        raise ValidationError(msg, field=field, value=value)


def validate_in_range(
    value: float | int,
    min_value: float | int,
    max_value: float | int,
    field: str,
) -> None:
    """Validate that a number is within a range.

    Args:
        value: The numeric value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field: The field name for error messages

    Raises:
        ValidationError: If the value is outside the range
    """
    if value < min_value or value > max_value:
        msg = f"{field} must be between {min_value} and {max_value}"
        raise ValidationError(msg, field=field, value=value)


def validate_one_of(value: object, allowed_values: Sequence[object], field: str) -> None:
    """Validate that a value is one of the allowed values.

    Args:
        value: The value to validate
        allowed_values: List of allowed values
        field: The field name for error messages

    Raises:
        ValidationError: If the value is not in the allowed list
    """
    if value not in allowed_values:
        msg = f"{field} must be one of {allowed_values}"
        raise ValidationError(msg, field=field, value=value)
