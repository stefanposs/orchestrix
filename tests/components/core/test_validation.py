"""Tests for validation utilities."""

import pytest

from orchestrix.core.validation import (
    ValidationError,
    validate_in_range,
    validate_max_length,
    validate_min_length,
    validate_non_negative,
    validate_not_empty,
    validate_one_of,
    validate_positive,
)


class TestValidationError:
    """Test ValidationError exception."""

    def test_error_with_field_and_value(self) -> None:
        """Test error with field and value."""
        error = ValidationError("Invalid value", field="amount", value=-10)

        assert error.message == "Invalid value"
        assert error.field == "amount"
        assert error.value == -10
        assert str(error) == "Validation failed for 'amount': Invalid value"

    def test_error_without_field(self) -> None:
        """Test error without field."""
        error = ValidationError("Something went wrong")

        assert error.message == "Something went wrong"
        assert error.field is None
        assert error.value is None
        assert str(error) == "Something went wrong"


class TestValidateNotEmpty:
    """Test validate_not_empty function."""

    def test_valid_string(self) -> None:
        """Valid non-empty string should not raise."""
        validate_not_empty("hello", "name")  # Should not raise

    def test_empty_string_raises(self) -> None:
        """Empty string should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_not_empty("", "name")

        assert "name cannot be empty" in str(exc_info.value)
        assert exc_info.value.field == "name"

    def test_whitespace_only_raises(self) -> None:
        """Whitespace-only string should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_not_empty("   ", "name")

        assert "name cannot be empty" in str(exc_info.value)


class TestValidatePositive:
    """Test validate_positive function."""

    def test_positive_number(self) -> None:
        """Positive number should not raise."""
        validate_positive(10, "amount")
        validate_positive(0.1, "amount")

    def test_zero_raises(self) -> None:
        """Zero should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive(0, "amount")

        assert "amount must be positive" in str(exc_info.value)
        assert exc_info.value.field == "amount"

    def test_negative_raises(self) -> None:
        """Negative number should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive(-5, "amount")

        assert "amount must be positive" in str(exc_info.value)


class TestValidateNonNegative:
    """Test validate_non_negative function."""

    def test_positive_number(self) -> None:
        """Positive number should not raise."""
        validate_non_negative(10, "quantity")

    def test_zero_is_valid(self) -> None:
        """Zero should be valid."""
        validate_non_negative(0, "quantity")

    def test_negative_raises(self) -> None:
        """Negative number should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_negative(-1, "quantity")

        assert "quantity cannot be negative" in str(exc_info.value)


class TestValidateMinLength:
    """Test validate_min_length function."""

    def test_valid_length(self) -> None:
        """String meeting minimum length should not raise."""
        validate_min_length("hello", 3, "username")
        validate_min_length("abc", 3, "username")

    def test_too_short_raises(self) -> None:
        """String shorter than minimum should raise."""
        with pytest.raises(ValidationError) as exc_info:
            validate_min_length("ab", 3, "username")

        assert "username must be at least 3 characters" in str(exc_info.value)


class TestValidateMaxLength:
    """Test validate_max_length function."""

    def test_valid_length(self) -> None:
        """String within maximum length should not raise."""
        validate_max_length("hello", 10, "username")
        validate_max_length("a" * 10, 10, "username")

    def test_too_long_raises(self) -> None:
        """String longer than maximum should raise."""
        with pytest.raises(ValidationError) as exc_info:
            validate_max_length("a" * 11, 10, "username")

        assert "username must be at most 10 characters" in str(exc_info.value)


class TestValidateInRange:
    """Test validate_in_range function."""

    def test_value_in_range(self) -> None:
        """Value within range should not raise."""
        validate_in_range(5, 1, 10, "rating")
        validate_in_range(1, 1, 10, "rating")  # Min boundary
        validate_in_range(10, 1, 10, "rating")  # Max boundary

    def test_value_below_range_raises(self) -> None:
        """Value below minimum should raise."""
        with pytest.raises(ValidationError) as exc_info:
            validate_in_range(0, 1, 10, "rating")

        assert "rating must be between 1 and 10" in str(exc_info.value)

    def test_value_above_range_raises(self) -> None:
        """Value above maximum should raise."""
        with pytest.raises(ValidationError) as exc_info:
            validate_in_range(11, 1, 10, "rating")

        assert "rating must be between 1 and 10" in str(exc_info.value)


class TestValidateOneOf:
    """Test validate_one_of function."""

    def test_value_in_allowed_list(self) -> None:
        """Value in allowed list should not raise."""
        validate_one_of("active", ["active", "inactive", "pending"], "status")

    def test_value_not_in_list_raises(self) -> None:
        """Value not in allowed list should raise."""
        allowed = ["active", "inactive", "pending"]
        with pytest.raises(ValidationError) as exc_info:
            validate_one_of("deleted", allowed, "status")

        assert "status must be one of" in str(exc_info.value)
        assert exc_info.value.field == "status"
