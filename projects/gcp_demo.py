"""Beispiel für die Nutzung des CloudSQL EventStore mit Orchestrix (GCP Demo)."""

import asyncio
from orchestrix.infrastructure.gcp_cloud_sql import GCPCloudSQLEventStore


async def main() -> None:
    """Fügt ein Demo-Event ein und gibt alle Events aus dem Stream aus."""
    store = GCPCloudSQLEventStore()
    await store.append("demo-stream", {"type": "DemoEvent", "data": {"msg": "Hallo GCP!"}})
    events = [e async for e in store.load("demo-stream")]
    print("Events in demo-stream:", events)


if __name__ == "__main__":
    asyncio.run(main())
