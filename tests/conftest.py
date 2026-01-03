"""Test configuration and fixtures."""

import pytest

from orchestrix.infrastructure import InMemoryEventStore, InMemoryMessageBus


@pytest.fixture
def bus():
    """Provide a fresh InMemoryMessageBus for each test."""
    return InMemoryMessageBus()


@pytest.fixture
def store():
    """Provide a fresh InMemoryEventStore for each test."""
    return InMemoryEventStore()
