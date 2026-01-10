import asyncio
from collections.abc import Callable
from typing import Any


class GCPPubSub:
    """Google Cloud Pub/Sub Store for publishing and subscribing messages."""

    def __init__(
        self,
        project_id: str = "",
        topic: str = "",
        subscription: str = "",
        publisher: Any = None,
        subscriber: Any = None,
    ):
        self.project_id = project_id
        self.topic = topic
        self.subscription = subscription
        self.publisher = publisher
        self.subscriber = subscriber

        self.topic_path = f"projects/{project_id}/topics/{topic}" if project_id and topic else ""
        self.subscription_path = (
            f"projects/{project_id}/subscriptions/{subscription}"
            if project_id and subscription
            else ""
        )

    async def publish(self, message: dict[str, Any]) -> None:
        """Publish a message to the configured Pub/Sub topic."""
        loop = asyncio.get_running_loop()
        data = str(message).encode("utf-8")
        await loop.run_in_executor(None, lambda: self.publisher.publish(self.topic_path, data))

    async def subscribe(self, callback: Callable[[bytes], None]) -> None:
        """Subscribe to the configured Pub/Sub subscription and call the callback for each message."""

        def _callback(message: Any) -> None:
            callback(message.data)
            message.ack()

        future = self.subscriber.subscribe(self.subscription_path, callback=_callback)
        try:
            await asyncio.get_running_loop().run_in_executor(None, future.result)
        except Exception:
            future.cancel()
