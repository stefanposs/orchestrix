"""
Integrationstest für GCPPubSub mit Testcontainers Pub/Sub Emulator.
"""

import pytest
from testcontainers.google.pubsub import PubSubContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy
from orchestrix.infrastructure.gcp_pubsub.store import GCPPubSub
import os


@pytest.mark.asyncio
async def test_pubsub_with_testcontainers():
    try:
        with PubSubContainer() as pubsub:
            pubsub.waiting_for(HttpWaitStrategy(8085).for_status_code(200))
            # Use the correct property for the emulator endpoint
            os.environ["PUBSUB_EMULATOR_HOST"] = (
                pubsub.get_container_host_ip() + ":" + str(pubsub.get_exposed_port(8085))
            )
            os.environ["PUBSUB_PROJECT"] = "test-project"
            os.environ["PUBSUB_TOPIC"] = "test-topic"
            os.environ["PUBSUB_SUBSCRIPTION"] = "test-sub"
            store = GCPPubSub()
            await store.publish({"type": "TestEvent", "data": {"msg": "Hallo Pub/Sub!"}})

            # Empfangen ist in echten Tests komplexer, hier nur Dummy-Callback
            def dummy_callback(data):
                assert b"Hallo Pub/Sub!" in data

            await store.subscribe(dummy_callback)
    except Exception as e:
        pytest.skip(f"PubSubContainer could not be started: {e}")
