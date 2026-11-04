import math
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from game_discovery.api.main import create_app
from game_discovery.catalog.contracts import DiscoverRequest
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.retrieval.query import BoundedQueryEncoder, lexical_query


class HybridM4Tests(unittest.TestCase):
    def test_text_is_bounded_and_provider_instructions_do_not_become_sql(self):
        query = "combat'); DROP TABLE games; -- progression | combat"
        terms = lexical_query(query)
        self.assertEqual(terms, "combat | drop | table | games | progression")
        self.assertEqual(len(lexical_query(" ".join(f"word{n}" for n in range(1000))).split(" | ")), 1)
        repository = MagicMock(spec=CatalogRepository)
        with TestClient(create_app(Settings(), repository=repository)) as client:
            self.assertEqual(client.post("/api/v1/discover", json={"query": "a" * 2001}).status_code, 422)
            repository.discover.assert_not_called()

    def test_text_query_ranks_without_relaxing_hard_controls(self):
        connection = MagicMock()
        connection.execute.side_effect = [[], []]

        class Repository(CatalogRepository):
            @contextmanager
            def snapshot(self):
                yield connection, "fixture"

        Repository(MagicMock()).discover(DiscoverRequest.model_validate({
            "query": "combat progression", "filters": {"platforms": ["windows"], "max_price_cents": 1999}}),
            query_vector=[1.0] + [0.0] * 383, encoder_version="fixture")
        statement, params = connection.execute.call_args.args
        self.assertEqual(params["query_terms"], "combat | progression")
        self.assertEqual(params["budget"], 1999)
        self.assertEqual(params["platforms"], ["windows"])
        self.assertIn("ts_rank_cd", str(statement))
        self.assertIn("left join discovery.game_prices", str(statement))
        self.assertIn("order by", str(statement))
        self.assertNotIn("combat", str(statement))

    def test_encoder_rejects_invalid_vectors_and_releases_slot_after_failure(self):
        for vector in ([0.0] * 384, [math.nan] * 384, [1.0], [math.inf] * 384):
            encoder = BoundedQueryEncoder(lambda _: vector, "fixture")
            with self.assertRaises(ValueError):
                encoder("combat")
            self.assertTrue(encoder.slot.acquire(blocking=False))
            encoder.slot.release()

    def test_busy_encoder_falls_back_and_explicit_filters_are_preserved(self):
        encoder = BoundedQueryEncoder(lambda _: [1.0] + [0.0] * 383, "fixture")
        encoder.slot.acquire()
        repository = MagicMock(spec=CatalogRepository)
        repository.discover.return_value = ("fixture", [])
        try:
            with TestClient(create_app(Settings(), repository=repository, query_encoder=encoder)) as client:
                response = client.post("/api/v1/discover", json={
                    "query": "Less repetition under $20", "filters": {"max_price_cents": 1000}})
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["ranking_version"], "hybrid-text-v1")
                self.assertEqual(body["effective_criteria"]["max_price_cents"], 1000)
                self.assertTrue(any("repetition" in item for item in body["unresolved_preferences"]))
                self.assertTrue(any("lexical" in item for item in body["degraded_reasons"]))
        finally:
            encoder.slot.release()

    def test_catalog_activation_mismatch_retries_only_with_safe_lexical_fallback(self):
        encoder = BoundedQueryEncoder(lambda _: [1.0] + [0.0] * 383, "old")
        repository = MagicMock(spec=CatalogRepository)
        repository.discover.side_effect = [CatalogFailure("query_artifact_mismatch"), ("new", [])]
        with TestClient(create_app(Settings(), repository=repository, query_encoder=encoder)) as client:
            response = client.post("/api/v1/discover", json={"query": "combat"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(any("active catalog" in item for item in response.json()["degraded_reasons"]))
            self.assertEqual(repository.discover.call_count, 2)
            self.assertFalse(repository.discover.call_args.kwargs)

    def test_failed_encoder_load_keeps_core_discovery_available(self):
        repository = MagicMock(spec=CatalogRepository)
        repository.discover.return_value = ("fixture", [])
        settings = Settings(query_model_path="missing", query_tokenizer_path="missing", query_artifact_path="missing")
        with TestClient(create_app(settings, repository=repository)) as client:
            response = client.post("/api/v1/discover", json={"query": "story"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(any("lexical" in item for item in response.json()["degraded_reasons"]))
