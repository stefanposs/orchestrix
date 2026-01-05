"""Tests for InMemoryEventStore."""

from orchestrix.core.messaging.message import Event


class TestInMemoryEventStore:
    """Tests for in-memory event store implementation."""

    def test_save_and_load_events(self, store):
        """Test saving and loading events for an aggregate."""
        aggregate_id = "agg-123"
        events = [
            Event(id="evt-1"),
            Event(id="evt-2"),
            Event(id="evt-3"),
        ]

        store.save(aggregate_id, events)
        loaded = store.load(aggregate_id)

        assert len(loaded) == 3
        assert loaded[0].id == "evt-1"
        assert loaded[1].id == "evt-2"
        assert loaded[2].id == "evt-3"

    def test_load_nonexistent_aggregate(self, store):
        """Test loading events for an aggregate that doesn't exist."""
        loaded = store.load("nonexistent")

        assert loaded == []

    def test_save_multiple_times(self, store):
        """Test saving events multiple times appends them."""
        aggregate_id = "agg-123"

        store.save(aggregate_id, [Event(id="evt-1")])
        store.save(aggregate_id, [Event(id="evt-2")])
        store.save(aggregate_id, [Event(id="evt-3")])

        loaded = store.load(aggregate_id)

        assert len(loaded) == 3
        assert [e.id for e in loaded] == ["evt-1", "evt-2", "evt-3"]

    def test_different_aggregates_isolated(self, store):
        """Test that different aggregates have isolated event streams."""
        store.save("agg-1", [Event(id="evt-1")])
        store.save("agg-2", [Event(id="evt-2")])
        store.save("agg-1", [Event(id="evt-3")])

        agg1_events = store.load("agg-1")
        agg2_events = store.load("agg-2")

        assert len(agg1_events) == 2
        assert len(agg2_events) == 1
        assert [e.id for e in agg1_events] == ["evt-1", "evt-3"]
        assert [e.id for e in agg2_events] == ["evt-2"]

    def test_save_empty_list(self, store):
        """Test saving an empty list of events."""
        store.save("agg-123", [])
        loaded = store.load("agg-123")

        assert loaded == []
