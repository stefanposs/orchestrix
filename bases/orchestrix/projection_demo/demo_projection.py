"""Projection Demo for orchestrix.

Demonstrates how to build read models (projections) from events.
"""

from dataclasses import dataclass, field

from orchestrix.core.messaging import Event
from orchestrix.infrastructure.memory import InMemoryMessageBus


@dataclass(frozen=True, kw_only=True)
class AccountCreated(Event):
    """Event when an account is created."""

    account_id: str
    owner: str


@dataclass(frozen=True, kw_only=True)
class MoneyDeposited(Event):
    """Event when money is deposited."""

    account_id: str
    amount: float


@dataclass(frozen=True, kw_only=True)
class MoneyWithdrawn(Event):
    """Event when money is withdrawn."""

    account_id: str
    amount: float


@dataclass
class AccountProjection:
    """Read model for account balance."""

    balances: dict[str, float] = field(default_factory=dict)
    owners: dict[str, str] = field(default_factory=dict)

    def apply_created(self, event: AccountCreated) -> None:
        """Apply AccountCreated event."""
        self.balances[event.account_id] = 0.0
        self.owners[event.account_id] = event.owner

    def apply_deposited(self, event: MoneyDeposited) -> None:
        """Apply MoneyDeposited event."""
        self.balances[event.account_id] += event.amount

    def apply_withdrawn(self, event: MoneyWithdrawn) -> None:
        """Apply MoneyWithdrawn event."""
        self.balances[event.account_id] -= event.amount

    def get_balance(self, account_id: str) -> float:
        """Get current balance for account."""
        return self.balances.get(account_id, 0.0)


def demo_projection() -> None:
    """Demonstrate building projections from events."""
    print("\n=== Projection Demo ===\n")

    bus = InMemoryMessageBus()
    projection = AccountProjection()

    # Subscribe projection handlers
    bus.subscribe(AccountCreated, projection.apply_created)
    bus.subscribe(MoneyDeposited, projection.apply_deposited)
    bus.subscribe(MoneyWithdrawn, projection.apply_withdrawn)

    # Replay events to build projection
    events = [
        AccountCreated(account_id="ACC-001", owner="Alice"),
        MoneyDeposited(account_id="ACC-001", amount=1000.0),
        MoneyDeposited(account_id="ACC-001", amount=500.0),
        MoneyWithdrawn(account_id="ACC-001", amount=200.0),
        AccountCreated(account_id="ACC-002", owner="Bob"),
        MoneyDeposited(account_id="ACC-002", amount=250.0),
    ]

    print("Replaying events:")
    for event in events:
        print(f"  → {type(event).__name__}: {event}")
        bus.publish(event)

    # Query projection
    print("\nProjection state:")
    print(f"  Alice (ACC-001): ${projection.get_balance('ACC-001'):.2f}")
    print(f"  Bob (ACC-002): ${projection.get_balance('ACC-002'):.2f}")


if __name__ == "__main__":
    demo_projection()
