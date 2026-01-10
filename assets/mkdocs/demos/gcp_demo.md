
# GCP CloudSQL Demo

This example shows how to use the CloudSQL EventStore in Orchestrix:

```python
import asyncio
from orchestrix.infrastructure.gcp_cloud_sql import GCPCloudSQLEventStore

async def main():
    store = GCPCloudSQLEventStore()
    await store.append("demo-stream", {"type": "DemoEvent", "data": {"msg": "Hello GCP!"}})
    events = [e async for e in store.load("demo-stream")]
    print("Events in demo-stream:", events)

if __name__ == "__main__":
    asyncio.run(main())
```

> **Note:** You must set the environment variables for the CloudSQL connection (see README in the gcp_cloud_sql folder).
