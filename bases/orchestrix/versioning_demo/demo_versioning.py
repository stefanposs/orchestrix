"""Event Versioning Demo for orchestrix.

Demonstrates event versioning strategy:
Multi-Handler: Supporting both event versions in parallel
"""

from dataclasses import dataclass

from orchestrix.core.messaging import Event
from orchestrix.infrastructure.memory import InMemoryMessageBus


@dataclass(frozen=True, kw_only=True)
class UserCreatedV1(Event):
    """Initial version of user created event."""

    user_id: str
    email: str


@dataclass(frozen=True, kw_only=True)
class UserCreatedV2(Event):
    """Extended version with additional fields."""

    user_id: str
    email: str
    username: str
    created_at: str


def demo_multi_handler() -> None:
    """Demonstrate parallel support for both event versions."""
    print("\n=== Multi-Handler Strategy ===\n")

    bus = InMemoryMessageBus()

    # Register handlers for both versions
    bus.subscribe(UserCreatedV1, lambda e: print(f"  → V1 Handler: {e.email}"))
    bus.subscribe(UserCreatedV2, lambda e: print(f"  → V2 Handler: {e.username} ({e.email})"))

    # Publish both event versions - each routed to its respective handler
    v1 = UserCreatedV1(user_id="1", email="old@example.com")
    v2 = UserCreatedV2(
        user_id="2",
        email="new@example.com",
        username="new_user",
        created_at="2026-02-05",
    )

    print(f"Publishing V1: {v1}")
    bus.publish(v1)

    print(f"Publishing V2: {v2}")
    bus.publish(v2)


if __name__ == "__main__":
    demo_multi_handler()
