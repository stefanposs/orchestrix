"""GCP BigQuery Event Store für Orchestrix. Verwendet google-cloud-bigquery für asynchrone Event-Speicherung. Alle Events werden als JSON-String gespeichert."""

import os
import json
import uuid
from datetime import datetime, UTC
from collections.abc import AsyncIterator
import asyncio

# Hinweis: Ty meldet für den folgenden Import einen 'unresolved-import'-Fehler,
# weil Google keine vollständigen Typstubs für 'google.cloud.bigquery' bereitstellt.
# Das beeinträchtigt weder Lint noch Funktionalität und ist unbedenklich.
from google.cloud import bigquery


import re


class GCPBigQueryEventStore:
    """Asynchroner EventStore für Google BigQuery.

    Sicherheit: Dataset- und Tabellennamen werden strikt auf [a-zA-Z0-9_] geprüft, um SQL-Injection zu verhindern.
    """

    _BQ_NAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")

    def __init__(self, dataset: str | None = None, table: str | None = None):
        self.dataset = dataset or os.getenv("BQ_DATASET", "orchestrix")
        self.table = table or os.getenv("BQ_TABLE", "orchestrix_events")
        if not self._BQ_NAME_RE.match(self.dataset):
            raise ValueError(f"Ungültiger Dataset-Name: {self.dataset}")
        if not self._BQ_NAME_RE.match(self.table):
            raise ValueError(f"Ungültiger Tabellen-Name: {self.table}")
        self.client = bigquery.Client()

    async def append(self, stream: str, event: dict) -> None:
        """Fügt ein Event in BigQuery ein."""
        row = {
            "event_id": str(uuid.uuid4()),
            "stream": stream,
            "version": await self._next_version(stream),
            "type": event["type"],
            "data": json.dumps(event["data"]),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        # BigQuery Python-Client ist nicht async, daher run_in_executor
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, lambda: self.client.insert_rows_json(f"{self.dataset}.{self.table}", [row])
        )

    async def load(self, stream: str, from_version: int = 0) -> AsyncIterator[dict]:
        """Lädt Events aus BigQuery für einen Stream."""
        query = (
            "SELECT version, type, data, timestamp "
            f"FROM `{self.dataset}.{self.table}` "
            "WHERE stream = @stream AND version >= @from_version "
            "ORDER BY version ASC"
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("stream", "STRING", stream),
                bigquery.ScalarQueryParameter("from_version", "INT64", from_version + 1),
            ]
        )
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: list(self.client.query(query, job_config=job_config))
        )
        for row in result:
            yield {
                "version": row.version,
                "type": row.type,
                "data": json.loads(row.data),
                "timestamp": row.timestamp,
            }

    async def _next_version(self, stream: str) -> int:
        query = (
            "SELECT COALESCE(MAX(version), 0) + 1 as next_version "
            f"FROM `{self.dataset}.{self.table}` "
            "WHERE stream = @stream"
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("stream", "STRING", stream),
            ]
        )
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: list(self.client.query(query, job_config=job_config))
        )
        return result[0].next_version if result else 1
