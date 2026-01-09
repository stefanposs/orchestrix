# GCP CloudSQL Demo

Dieses Beispiel zeigt, wie der CloudSQL EventStore von Orchestrix verwendet wird:

```python
import asyncio
from orchestrix.infrastructure.gcp_cloud_sql import GCPCloudSQLEventStore

async def main():
    store = GCPCloudSQLEventStore()
    await store.append("demo-stream", {"type": "DemoEvent", "data": {"msg": "Hallo GCP!"}})
    events = [e async for e in store.load("demo-stream")]
    print("Events in demo-stream:", events)

if __name__ == "__main__":
    asyncio.run(main())
```

> **Hinweis:** Die Umgebungsvariablen für die CloudSQL-Verbindung müssen gesetzt sein (siehe README im cloudsql-Ordner).
> **Hinweis:** Die Umgebungsvariablen für die CloudSQL-Verbindung müssen gesetzt sein (siehe README im gcp_cloud_sql-Ordner).
