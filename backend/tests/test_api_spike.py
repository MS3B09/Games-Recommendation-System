import unittest

import numpy as np
from fastapi.testclient import TestClient

from game_discovery.jobs.api_spike import create_app


class FakeEncoder:
    def encode(self, _):
        return np.ones((1, 384), dtype=np.float32) / 384**0.5


class ResourceSpikeTests(unittest.TestCase):
    def test_live_health_does_not_claim_catalog_readiness(self):
        with TestClient(create_app(lambda: FakeEncoder(), lambda: False)) as client:
            self.assertEqual(client.get("/health/live").status_code, 200)
            ready = client.get("/health/ready")
            self.assertEqual(ready.status_code, 503)
            self.assertFalse(ready.json()["database_available"])
            self.assertFalse(ready.json()["catalog_active"])

    def test_unavailable_encoder_returns_503_instead_of_fake_vectors(self):
        def unavailable():
            raise OSError("missing model")
        with TestClient(create_app(unavailable, lambda: True)) as client:
            response = client.post("/spike/encode", json={"text": "combat"})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("embedding", response.json())

    def test_concurrent_inference_is_bounded_and_input_is_validated(self):
        app = create_app(lambda: FakeEncoder(), lambda: True)
        with TestClient(app) as client:
            app.state.inference_slot.acquire()
            try:
                self.assertEqual(client.post("/spike/encode", json={"text": "combat"}).status_code, 429)
            finally:
                app.state.inference_slot.release()
            self.assertEqual(client.post("/spike/encode", json={"text": "x" * 16001}).status_code, 422)
            self.assertEqual(client.post("/spike/encode", json={"text": "combat"}).json()["dimensions"], 384)
