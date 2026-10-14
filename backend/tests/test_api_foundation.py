import unittest

from fastapi.testclient import TestClient
from pydantic import SecretStr

from game_discovery.api.main import create_app
from game_discovery.core.settings import Settings
from game_discovery.db.readiness import CatalogReadiness


class ApiFoundationTests(unittest.TestCase):
    def client(self, probe):
        return TestClient(create_app(Settings(), catalog_probe=probe))

    def test_liveness_never_depends_on_database(self):
        def broken():
            raise AssertionError("liveness must not query the DB")
        with self.client(broken) as client:
            self.assertEqual(client.get("/health/live").json(), {"status": "alive"})

    def test_empty_catalog_is_not_database_unavailability(self):
        with self.client(lambda: CatalogReadiness()) as client:
            self.assertEqual(client.get("/health/ready").json()["code"], "catalog_not_initialized")
            response = client.get("/api/v1/catalog/status")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["state"], "uninitialized")
            self.assertIsNone(response.json()["source_observed_at"])

    def test_errors_have_request_ids_and_do_not_expose_credentials(self):
        settings = Settings(database_url=SecretStr("postgresql://user:secret-value@db.example.test/postgres"))
        app = create_app(settings, lambda: CatalogReadiness(error_code="database_unavailable", retryable=True))
        with TestClient(app) as client:
            response = client.get("/api/v1/catalog/status")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["request_id"], response.headers["X-Request-ID"])
            self.assertTrue(response.json()["retryable"])
            self.assertNotIn("secret-value", response.text)
            self.assertNotIn("secret-value", repr(settings))

    def test_ready_catalog_does_not_require_an_llm(self):
        with self.client(lambda: CatalogReadiness(version="fixture-v1", game_count=3)) as client:
            self.assertEqual(client.get("/health/ready").status_code, 200)
            self.assertFalse(client.get("/api/v1/catalog/status").json()["llm_enabled"])

    def test_invalid_dsn_does_not_take_down_liveness_or_expose_input(self):
        for value in ("not-a-url-secret", "sqlite:///not-a-runtime-database"):
            with TestClient(create_app(Settings(database_url=SecretStr(value)))) as client:
                self.assertEqual(client.get("/health/live").status_code, 200)
                response = client.get("/api/v1/catalog/status")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["code"], "database_configuration_invalid")
                self.assertNotIn(value, response.text)

    def test_browser_cors_is_explicit(self):
        with self.client(CatalogReadiness) as client:
            allowed = client.get("/api/v1/catalog/status", headers={"Origin": "http://localhost:5173"})
            blocked = client.get("/api/v1/catalog/status", headers={"Origin": "https://other.example"})
            self.assertEqual(allowed.headers["access-control-allow-origin"], "http://localhost:5173")
            self.assertNotIn("access-control-allow-origin", blocked.headers)
