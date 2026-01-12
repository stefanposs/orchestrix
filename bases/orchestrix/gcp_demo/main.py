"""Beispiel für die Nutzung von CloudSQL und BigQuery EventStore mit Orchestrix (GCP Demo)."""

import asyncio
from orchestrix.infrastructure.gcp_cloud_sql import GCPCloudSQLEventStore
from orchestrix.infrastructure.gcp_bigquery.store import GCPBigQueryEventStore


async def cloudsql_demo():
    """Fügt ein Demo-Event in CloudSQL ein und gibt alle Events aus dem Stream aus."""
    store = GCPCloudSQLEventStore()
    await store.append("cloudsql-stream", {"type": "DemoEvent", "data": {"msg": "Hallo CloudSQL!"}})
    events = [e async for e in store.load("cloudsql-stream")]
    print("Events in cloudsql-stream:", events)


async def bigquery_demo():
    """Fügt ein Demo-Event in BigQuery ein und gibt alle Events aus dem Stream aus."""
    store = GCPBigQueryEventStore()
    await store.append("bigquery-stream", {"type": "DemoEvent", "data": {"msg": "Hallo BigQuery!"}})
    events = [e async for e in store.load("bigquery-stream")]
    print("Events in bigquery-stream:", events)


async def main():
    """Runs both CloudSQL and BigQuery demo examples for Orchestrix GCP integration."""
    await cloudsql_demo()
    await bigquery_demo()


if __name__ == "__main__":
    asyncio.run(main())
