# store.py for GCP PubSub integration


from typing import Any
from collections.abc import Callable


class GCPPubSub:
    """Stub for GCP PubSub integration. Implement methods as needed."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def publish(self, message: Any) -> None:
        """Publish a message to a topic (stub)."""

    async def subscribe(self, callback: Callable[[Any], None]) -> None:
        """Subscribe to a topic (stub)."""
