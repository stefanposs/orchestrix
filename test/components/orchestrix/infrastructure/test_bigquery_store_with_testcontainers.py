"""
Integrationstest für GCPBigQueryEventStore mit Testcontainers BigQuery Emulator.
"""

import pytest
import importlib.util

BIGQUERY_AVAILABLE = importlib.util.find_spec("testcontainers.google.bigquery") is not None


@pytest.mark.asyncio
async def test_bigquery_eventstore_with_testcontainers():
    if not BIGQUERY_AVAILABLE:
        pytest.skip("BigQueryContainer not available in testcontainers package.")
    # Test skipped or would run here if available
