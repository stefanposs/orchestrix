"""Validation Demo for orchestrix.

Demonstrates how to validate events before processing.
"""

from dataclasses import dataclass

from orchestrix.core.messaging import Event
from orchestrix.infrastructure.memory import InMemoryMessageBus


class ValidationError(Exception):
    """Raised when event validation fails."""


@dataclass(frozen=True, kw_only=True)
class UserRegistered(Event):
    """Event when a user registers."""

    email: str
    age: int
    username: str


def validate_user_registered(event: UserRegistered) -> None:
    """Validate UserRegistered event."""
    errors: list[str] = []

    if "@" not in event.email:
        errors.append("Invalid email format")
    if event.age < 18:
        errors.append("User must be 18 or older")
    if len(event.username) < 3:
        errors.append("Username must be at least 3 characters")

    if errors:
        raise ValidationError(f"Validation failed: {', '.join(errors)}")


def demo_validation() -> None:
    """Demonstrate event validation."""
    print("\n=== Event Validation Demo ===\n")

    bus = InMemoryMessageBus()

    # Handler with validation
    def handle_user_registered(event: UserRegistered) -> None:
        try:
            validate_user_registered(event)
            print(f"  ✓ Valid: {event.username} ({event.email})")
        except ValidationError as e:
            print(f"  ✗ Invalid: {e}")

    bus.subscribe(UserRegistered, handle_user_registered)

    # Test valid event
    print("Publishing valid event:")
    bus.publish(UserRegistered(email="john@example.com", age=25, username="johndoe"))

    # Test invalid events
    print("\nPublishing invalid events:")
    bus.publish(UserRegistered(email="invalid-email", age=25, username="john"))
    bus.publish(UserRegistered(email="jane@example.com", age=16, username="jane"))
    bus.publish(UserRegistered(email="bad", age=15, username="ab"))


if __name__ == "__main__":
    demo_validation()
