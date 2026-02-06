"""Beispiel für die Nutzung von GCP Pub/Sub mit Orchestrix (GCP Demo)."""

import asyncio
from orchestrix.infrastructure.gcp_pubsub.store import GCPPubSub


async def main() -> None:
    """Run Pub/Sub demo: publish and receive a message."""
    pubsub = GCPPubSub(project_id="test-project", topic="test-topic", subscription="test-sub")
    await pubsub.publish({"type": "DemoEvent", "data": {"msg": "Hallo Pub/Sub!"}})
    print("Nachricht veröffentlicht auf Pub/Sub.")

    # Hinweis: Die subscribe-Methode ist für echte Event-Streams gedacht und blockiert ggf. länger.
    # Hier nur als Beispiel, wie man Nachrichten empfangen könnte.
    def print_message(data: bytes) -> None:
        print("Empfangen:", data)

    await pubsub.subscribe(print_message)


if __name__ == "__main__":
    asyncio.run(main())
