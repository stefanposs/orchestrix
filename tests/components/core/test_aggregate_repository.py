"""Tests for AggregateRepository with async operations.

This test module covers the async/sync methods of AggregateRepository
that had low coverage (lines 130-187).
"""

import pytest
from dataclasses import dataclass, field
from decimal import Decimal

from orchestrix.core.aggregate import AggregateRoot, AggregateRepository
from orchestrix.core.message import Event
from orchestrix.infrastructure.async_inmemory_store import InMemoryAsyncEventStore


# Domain model for testing
@dataclass(frozen=True, kw_only=True)
class AccountOpened(Event):
    """Account was opened."""

    account_id: str
    owner_name: str
    initial_balance: Decimal


@dataclass(frozen=True, kw_only=True)
class MoneyDeposited(Event):
    """Money was deposited."""

    account_id: str
    amount: Decimal


@dataclass(frozen=True, kw_only=True)
class MoneyWithdrawn(Event):
    """Money was withdrawn."""

    account_id: str
    amount: Decimal


@dataclass
class Account(AggregateRoot):
    """Account aggregate for testing."""

    owner_name: str = ""
    balance: Decimal = Decimal("0")

    def open(self, account_id: str, owner_name: str, initial_balance: Decimal) -> None:
        """Open account."""
        self._apply_event(
            AccountOpened(
                account_id=account_id,
                owner_name=owner_name,
                initial_balance=initial_balance,
            )
        )

    def deposit(self, amount: Decimal) -> None:
        """Deposit money."""
        self._apply_event(
            MoneyDeposited(
                account_id=self.aggregate_id,
                amount=amount,
            )
        )

    def withdraw(self, amount: Decimal) -> None:
        """Withdraw money."""
        self._apply_event(
            MoneyWithdrawn(
                account_id=self.aggregate_id,
                amount=amount,
            )
        )

    def _when_account_opened(self, event: AccountOpened) -> None:
        """Handle account opened."""
        self.aggregate_id = event.account_id
        self.owner_name = event.owner_name
        self.balance = event.initial_balance

    def _when_money_deposited(self, event: MoneyDeposited) -> None:
        """Handle money deposited."""
        self.balance += event.amount

    def _when_money_withdrawn(self, event: MoneyWithdrawn) -> None:
        """Handle money withdrawn."""
        self.balance -= event.amount


@pytest.fixture
def event_store():
    """Provide event store."""
    return InMemoryAsyncEventStore()


@pytest.fixture
def repository(event_store):
    """Provide repository."""
    return AggregateRepository(event_store=event_store)


class TestAggregateRepositoryAsync:
    """Test async repository operations."""

    @pytest.mark.asyncio
    async def test_load_async_single_event(self, repository: AggregateRepository):
        """Test loading aggregate with single event."""
        aggregate_id = "account-123"
        account = Account()
        account.aggregate_id = aggregate_id
        account.open(aggregate_id, "Alice", Decimal("100.00"))

        await repository.save_async(account)

        # Load it back
        loaded = await repository.load_async(Account, aggregate_id)

        assert loaded.aggregate_id == aggregate_id
        assert loaded.owner_name == "Alice"
        assert loaded.balance == Decimal("100.00")
        assert loaded.version == 1

    @pytest.mark.asyncio
    async def test_load_async_multiple_events(self, repository: AggregateRepository):
        """Test loading aggregate replays all events."""
        aggregate_id = "account-456"
        account = Account()
        account.aggregate_id = aggregate_id
        account.open(aggregate_id, "Bob", Decimal("500.00"))
        account.deposit(Decimal("100.00"))
        account.withdraw(Decimal("50.00"))

        await repository.save_async(account)

        # Load it back - should replay all 3 events
        loaded = await repository.load_async(Account, aggregate_id)

        assert loaded.balance == Decimal("550.00")  # 500 + 100 - 50
        assert loaded.version == 3

    @pytest.mark.asyncio
    async def test_load_async_not_found(self, repository: AggregateRepository):
        """Test loading non-existent aggregate raises error."""
        with pytest.raises(ValueError, match="not found"):
            await repository.load_async(Account, "nonexistent-id")

    @pytest.mark.asyncio
    async def test_save_async_clears_uncommitted_events(
        self, repository: AggregateRepository,
    ):
        """Test save_async clears uncommitted events."""
        aggregate_id = "account-789"
        account = Account()
        account.aggregate_id = aggregate_id
        account.open(aggregate_id, "Charlie", Decimal("200.00"))

        assert len(account.uncommitted_events) == 1

        await repository.save_async(account)

        assert len(account.uncommitted_events) == 0

    @pytest.mark.asyncio
    async def test_save_async_empty_uncommitted_is_noop(
        self, repository: AggregateRepository,
    ):
        """Test save_async with no uncommitted events is no-op."""
        aggregate_id = "account-empty"
        account = Account()
        account.aggregate_id = aggregate_id
        account.owner_name = "David"
        account.balance = Decimal("50.00")

        # No uncommitted events
        assert len(account.uncommitted_events) == 0

        # Should not raise error
        await repository.save_async(account)

    @pytest.mark.asyncio
    async def test_load_then_modify_then_save(self, repository: AggregateRepository):
        """Test load → modify → save cycle."""
        aggregate_id = "account-cycle"

        # Create and save
        account = Account()
        account.aggregate_id = aggregate_id
        account.open(aggregate_id, "Eve", Decimal("300.00"))
        await repository.save_async(account)

        # Load
        loaded = await repository.load_async(Account, aggregate_id)
        assert loaded.version == 1

        # Modify
        loaded.deposit(Decimal("100.00"))
        assert loaded.version == 2

        # Save
        await repository.save_async(loaded)

        # Load again - verify persistence
        loaded_again = await repository.load_async(Account, aggregate_id)
        assert loaded_again.balance == Decimal("400.00")
        assert loaded_again.version == 2

    @pytest.mark.asyncio
    async def test_load_async_replays_events_in_order(
        self, repository: AggregateRepository,
    ):
        """Test events are replayed in correct order."""
        aggregate_id = "account-order"
        account = Account()
        account.aggregate_id = aggregate_id
        account.open(aggregate_id, "Frank", Decimal("0"))
        account.deposit(Decimal("50"))
        account.deposit(Decimal("75"))
        account.withdraw(Decimal("25"))

        await repository.save_async(account)

        loaded = await repository.load_async(Account, aggregate_id)

        # 0 + 50 + 75 - 25 = 100
        assert loaded.balance == Decimal("100")


class TestAggregateRepositorySync:
    """Test sync repository operations with sync event store."""

    def test_load_sync_works(self):
        """Test synchronous load method."""
        from orchestrix.infrastructure.inmemory_store import InMemoryEventStore as SyncStore

        store = SyncStore()
        repository = AggregateRepository(event_store=store)

        aggregate_id = "account-sync"
        account = Account()
        account.aggregate_id = aggregate_id
        account.open(aggregate_id, "Grace", Decimal("150.00"))

        # Sync save
        repository.save(account)

        # Sync load
        loaded = repository.load(Account, aggregate_id)

        assert loaded.owner_name == "Grace"
        assert loaded.balance == Decimal("150.00")

    def test_save_sync_clears_uncommitted(self):
        """Test sync save clears uncommitted events."""
        from orchestrix.infrastructure.inmemory_store import InMemoryEventStore as SyncStore

        store = SyncStore()
        repository = AggregateRepository(event_store=store)

        aggregate_id = "account-sync-clear"
        account = Account()
        account.aggregate_id = aggregate_id
        account.open(aggregate_id, "Henry", Decimal("200.00"))

        assert len(account.uncommitted_events) == 1

        repository.save(account)

        assert len(account.uncommitted_events) == 0

    def test_load_sync_not_found(self):
        """Test sync load raises on not found."""
        from orchestrix.infrastructure.inmemory_store import InMemoryEventStore as SyncStore

        store = SyncStore()
        repository = AggregateRepository(event_store=store)

        with pytest.raises(ValueError, match="not found"):
            repository.load(Account, "nonexistent-sync")


class TestAggregateRootEventReplay:
    """Test event replay mechanisms in AggregateRoot."""

    @pytest.mark.asyncio
    async def test_replay_events_updates_version(self, event_store):
        """Test _replay_events increments version."""
        aggregate = Account()
        aggregate.aggregate_id = "test-id"

        events = [
            AccountOpened(
                account_id="test-id",
                owner_name="Test",
                initial_balance=Decimal("100"),
            ),
            MoneyDeposited(account_id="test-id", amount=Decimal("50")),
        ]

        aggregate._replay_events(events)

        assert aggregate.version == 2
        assert aggregate.balance == Decimal("150")

    @pytest.mark.asyncio
    async def test_apply_event_increments_version(self):
        """Test _apply_event increments version correctly."""
        aggregate = Account()
        aggregate.aggregate_id = "v-test"

        initial_version = aggregate.version
        aggregate._apply_event(
            AccountOpened(
                account_id="v-test",
                owner_name="Version Test",
                initial_balance=Decimal("1000"),
            )
        )

        assert aggregate.version == initial_version + 1
        assert len(aggregate.uncommitted_events) == 1

    def test_mark_events_committed(self):
        """Test mark_events_committed clears uncommitted events."""
        aggregate = Account()
        aggregate.uncommitted_events = [
            MoneyDeposited(account_id="test", amount=Decimal("10"))
        ]

        aggregate.mark_events_committed()

        assert len(aggregate.uncommitted_events) == 0

    def test_when_method_routes_to_handler(self):
        """Test _when method routes events to handlers."""
        aggregate = Account()
        aggregate.aggregate_id = "route-test"

        event = AccountOpened(
            account_id="route-test",
            owner_name="Route Test",
            initial_balance=Decimal("500"),
        )

        aggregate._when(event)

        # Handler should have been called
        assert aggregate.owner_name == "Route Test"
        assert aggregate.balance == Decimal("500")

    def test_to_snake_case_conversion(self):
        """Test snake case conversion for event routing."""
        aggregate = Account()

        assert aggregate._to_snake_case("AccountOpened") == "account_opened"
        assert aggregate._to_snake_case("MoneyDeposited") == "money_deposited"
        assert aggregate._to_snake_case("A") == "a"
        assert aggregate._to_snake_case("XMLParser") == "x_m_l_parser"

    def test_when_with_missing_handler(self):
        """Test _when silently ignores missing handlers."""
        aggregate = Account()

        # Create an event that doesn't have a handler
        class UnhandledEvent(Event):
            pass

        # Should not raise error
        aggregate._when(UnhandledEvent())
