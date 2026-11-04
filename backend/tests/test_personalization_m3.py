import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from pydantic import ValidationError

from game_discovery.api.main import create_app
from game_discovery.catalog.contracts import DiscoverRequest, Filters
from game_discovery.catalog.discovery import centroid, satisfies
from game_discovery.catalog.repository import CatalogRepository, filter_sql
from game_discovery.core.settings import Settings
from test_catalog_m2 import fixture


def feedback(app_id=10, kind="interested", timestamp="2026-10-15T10:00:00Z"):
    return {"app_id": app_id, "kind": kind, "timestamp": timestamp}


class PersonalizationM3Tests(unittest.TestCase):
    def test_price_range_is_inclusive_enforced_in_sql_and_rejects_unknown_prices(self):
        game = fixture()
        self.assertTrue(satisfies(game, Filters(min_price_cents=1999, max_price_cents=1999), set()))
        self.assertFalse(satisfies(game, Filters(min_price_cents=2000), set()))
        clauses, params = filter_sql(Filters(min_price_cents=1000, max_price_cents=2000))
        self.assertEqual(params["minimum_budget"], 1000)
        self.assertEqual(params["budget"], 2000)
        self.assertIn("p.amount_cents >= :minimum_budget", " ".join(clauses))
        game.price = None
        self.assertFalse(satisfies(game, Filters(min_price_cents=0), set()))

    def test_invalid_price_ranges_are_422_even_when_invalidity_only_appears_after_merge(self):
        repository = MagicMock(spec=CatalogRepository)
        with TestClient(create_app(Settings(), repository=repository)) as client:
            for body in ({"filters": {"min_price_cents": 2000, "max_price_cents": 1000}},
                         {"preferences": {"max_price_cents": 1000}, "filters": {"min_price_cents": 2000}},
                         {"filters": {"free_only": True, "min_price_cents": 100}},
                         {"filters": {"min_price_cents": -1}}):
                with self.subTest(body=body):
                    self.assertEqual(client.post("/api/v1/discover", json=body).status_code, 422)
            repository.discover.assert_not_called()
        request = DiscoverRequest.model_validate({"preferences": {"min_price_cents": 1000},
                                                   "filters": {"min_price_cents": None}})
        self.assertIsNone(request.effective_filters().min_price_cents)

    def test_required_genre_is_hard_while_preferred_terms_remain_soft(self):
        game = fixture()
        self.assertTrue(satisfies(game, Filters(required_genres=[" Action ", "action"]), set()))
        self.assertFalse(satisfies(game, Filters(required_genres=["puzzle"]), set()))
        self.assertTrue(satisfies(game, Filters(preferred_terms=["puzzle"]), set()))
        clauses, params = filter_sql(Filters(required_genres=["Action"]))
        self.assertIn("t.kind='genre'", clauses[0])
        self.assertEqual(params["genres"], ["action"])
        self.assertEqual(DiscoverRequest.model_validate({
            "preferences": {"required_genres": ["Action"]}, "filters": {"required_genres": []}
        }).effective_filters().required_genres, [])

    def test_explicit_empty_false_and_null_override_saved_controls(self):
        request = DiscoverRequest.model_validate({
            "preferences": {"max_price_cents": 1000, "free_only": True,
                            "platforms": ["linux"], "required_modes": ["single-player"]},
            "filters": {"max_price_cents": None, "free_only": False, "platforms": []}})
        effective = request.effective_filters()
        self.assertIsNone(effective.max_price_cents)
        self.assertFalse(effective.free_only)
        self.assertEqual(effective.platforms, [])
        self.assertEqual(effective.required_modes, ["single-player"])
        self.assertEqual(request.preferences.platforms, ["linux"])

    def test_feedback_coalesces_latest_and_keeps_exact_exclusions(self):
        request = DiscoverRequest.model_validate({"favorite_ids": [20],
            "filters": {"excluded_ids": [30]}, "feedback": [
                feedback(kind="not-for-me"), feedback(timestamp="2026-10-15T11:00:00Z"),
                feedback(kind="already-played", timestamp="2026-10-14T11:00:00Z"),
                feedback(40, "already-played"), feedback(50, "not-for-me")]})
        self.assertEqual(request.excluded_ids(), {20, 30, 40, 50})
        self.assertEqual(request.latest_feedback()[0].kind, "interested")

    def test_tied_timestamps_use_last_action(self):
        request = DiscoverRequest.model_validate({"feedback": [feedback(), feedback(kind="already-played")]})
        self.assertEqual(request.excluded_ids(), {10})

    def test_feedback_is_bounded_and_timestamps_require_timezone(self):
        for body in ({"feedback": [feedback()] * 501},
                     {"feedback": [feedback(timestamp="2026-10-15T10:00:00")]},
                     {"feedback": [feedback(kind="unknown")]},
                     {"preferences": {"platforms": ["invented"]}}):
            with self.subTest(body_keys=list(body)), self.assertRaises(ValidationError):
                DiscoverRequest.model_validate(body)

    def test_centroid_handles_missing_cancelled_and_normalized_vectors(self):
        self.assertIsNone(centroid([]))
        self.assertIsNone(centroid([[1.0, 0.0], [-1.0, 0.0]]))
        self.assertEqual(centroid([[1.0, 0.0], [1.0, 0.0]]), [1.0, 0.0])

    def test_repository_uses_bounded_affinity_and_no_negative_played_signal(self):
        game = fixture()
        for kind, expected in (("interested", "positive"), ("not-for-me", "negative"),
                               ("already-played", None)):
            connection = MagicMock()
            connection.execute.side_effect = [[(game.model_dump(mode="json"), "[1.0,0.0]")], []]

            class Repository(CatalogRepository):
                @contextmanager
                def snapshot(self):
                    yield connection, "fixture"

            Repository(MagicMock()).discover(DiscoverRequest.model_validate({
                "feedback": [feedback(kind=kind)], "preferences": {"max_price_cents": 2000}}))
            statement, params = connection.execute.call_args.args
            self.assertEqual(params["budget"], 2000)
            self.assertEqual(params["excluded"], [] if kind == "interested" else [10])
            self.assertEqual("positive" in params, expected == "positive")
            self.assertEqual("negative" in params, expected == "negative")
            if expected:
                self.assertIn("0.1 * greatest(0.0,least(1.0", str(statement))
            self.assertIn("order by", str(statement))

    def test_api_reports_effective_preferences_and_validates_without_echoing(self):
        repository = MagicMock(spec=CatalogRepository)
        repository.discover.return_value = ("fixture", [])
        with TestClient(create_app(Settings(), repository=repository)) as client:
            response = client.post("/api/v1/discover", json={
                "preferences": {"platforms": ["windows"], "max_price_cents": 1000},
                "filters": {"max_price_cents": 2000}})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["effective_criteria"]["platforms"], ["windows"])
            self.assertEqual(response.json()["effective_criteria"]["max_price_cents"], 2000)
            self.assertEqual(response.json()["ranking_version"], "seed-feedback-v1")
            invalid = client.post("/api/v1/discover", json={"feedback": [feedback(kind="do-not-echo")]})
            self.assertEqual(invalid.status_code, 422)
            self.assertNotIn("do-not-echo", invalid.text)
