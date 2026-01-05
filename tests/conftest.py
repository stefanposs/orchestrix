"""Test configuration and fixtures."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import pytest
from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus


@pytest.fixture
def bus():
    """Provide a fresh InMemoryMessageBus for each test."""
    return InMemoryMessageBus()


@pytest.fixture
def store():
    """Provide a fresh InMemoryEventStore for each test."""
    return InMemoryEventStore()


@dataclass
class FakeEventSourcingDBClient:
    """Fake EventSourcingDB Client for testing without SDK.

    Implements the same interface as the official eventsourcingdb.Client
    but stores events in memory.
    """

    def __init__(self) -> None:
        """Initialize fake client with in-memory storage."""
        self._events: dict[str, list[dict[str, Any]]] = {}  # subject -> events
        self._snapshots: dict[str, dict[str, Any]] = {}  # subject -> snapshot

    async def write_events(self, event_candidates: list[Any], **kwargs: Any) -> None:
        """Write events to in-memory store.

        Args:
            event_candidates: List of event dictionaries or EventCandidate objects
            **kwargs: Additional arguments (preconditions, etc.)
        """
        for candidate in event_candidates:
            if isinstance(candidate, dict):
                subject = candidate.get("subject", "")
                event_data = candidate
            else:
                # Handle EventCandidate object
                subject = getattr(candidate, "subject", "")
                event_data = {
                    "subject": subject,
                    "source": getattr(candidate, "source", ""),
                    "type": getattr(candidate, "type", ""),
                    "data": getattr(candidate, "data", {}),
                }
                # Copy other attributes if they exist
                for attr in ["id", "time", "specversion", "datacontenttype", "dataschema"]:
                    if hasattr(candidate, attr):
                        val = getattr(candidate, attr)
                        if val is not None:
                            event_data[attr] = val

            if subject not in self._events:
                self._events[subject] = []
            self._events[subject].append(event_data)

    async def read_events(
        self,
        subject: str | None = None,
        subject_filter: str | None = None,
        from_event_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Read events from in-memory store.

        Args:
            subject: Subject/aggregate ID to filter by (primary param name)
            subject_filter: Alternative param name for subject filter
            from_event_id: Read from specific event ID onwards
            **kwargs: Additional options (ignored)

        Yields:
            Event dictionaries matching filter
        """
        # Support both parameter names
        filter_subject = subject or subject_filter

        if filter_subject and filter_subject in self._events:
            events = self._events[filter_subject]
        else:
            events = []

        for event in events:
            yield event

    async def run_eventql_query(self, query: str, **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
        """Execute EventQL query (simplified for testing).

        Args:
            query: EventQL query string
            **kwargs: Additional options (ignored)

        Yields:
            Query results as dictionaries
        """
        # Simplified: just return empty results for now
        # In real implementation, would parse EventQL
        return
        yield  # Make this an async generator

    async def ping(self) -> str:
        """Check connection status.

        Returns:
            "pong" if connection successful
        """
        return "pong"

    async def read_last_snapshot(self, subject: str) -> dict[str, Any] | None:
        """Read last snapshot for subject.

        Args:
            subject: Aggregate ID

        Returns:
            Snapshot event or None if not found
        """
        return self._snapshots.get(subject)

    async def write_snapshot(self, subject: str, snapshot_event: dict[str, Any]) -> None:
        """Write snapshot for subject.

        Args:
            subject: Aggregate ID
            snapshot_event: Snapshot event dictionary
        """
        self._snapshots[subject] = snapshot_event


@pytest.fixture
def fake_esdb_client() -> FakeEventSourcingDBClient:
    """Provide fake EventSourcingDB client for testing."""
    return FakeEventSourcingDBClient()
