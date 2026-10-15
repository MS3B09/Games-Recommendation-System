import copy
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

from game_discovery.api.main import create_app
from game_discovery.catalog.contracts import Embedding, Filters, Source
from game_discovery.catalog.discovery import recommendation, satisfies
from game_discovery.core.settings import Settings
from game_discovery.jobs.catalog import normalize, normalize_payload, write_json


def payload():
    return {"10": {"success": True, "data": {
        "steam_appid": 10, "name": "Fixture", "short_description": "<b>A combat game.</b>",
        "type": "game", "is_free": False, "release_date": {"coming_soon": False},
        "content_descriptors": {"ids": [2, 5]}, "platforms": {"windows": True, "mac": False},
        "price_overview": {"currency": "USD", "final": 1999},
        "genres": [{"id": "1", "description": "Action"}], "categories": [{"id": 2}],
    }}}


def fixture(raw=None):
    return normalize_payload(10, raw or payload(), Source(
        url="https://store.steampowered.com/api/appdetails?appids=10&cc=us&l=english",
        collected_at=datetime(2026, 10, 14, tzinfo=UTC), sha256="a" * 64))


class CatalogM2Tests(unittest.TestCase):
    def test_constraints_never_infer_missing_facts(self):
        game = fixture()
        self.assertTrue(satisfies(game, Filters(max_price_cents=1999, platforms=["windows"], required_modes=["single-player"]), set()))
        self.assertFalse(satisfies(game, Filters(max_price_cents=1999, price_operator="lt"), set()))
        self.assertFalse(satisfies(game, Filters(platforms=["linux"]), set()))
        self.assertFalse(satisfies(game, Filters(required_modes=["online-co-op"]), set()))
        self.assertFalse(satisfies(game, Filters(free_only=True), set()))
        self.assertFalse(satisfies(game, Filters(), {10}))
        self.assertFalse(satisfies(game, Filters(unwanted_terms=["Action"]), set()))
        game.price = None
        self.assertFalse(satisfies(game, Filters(max_price_cents=2000), set()))

    def test_platform_any_all_and_preferred_not_mandatory(self):
        game = fixture()
        self.assertTrue(satisfies(game, Filters(platforms=["windows", "linux"], platform_match="any"), set()))
        self.assertFalse(satisfies(game, Filters(platforms=["windows", "linux"], platform_match="all"), set()))
        self.assertTrue(satisfies(game, Filters(preferred_terms=["puzzle"]), set()))

    def test_non_us_prices_and_promotion_are_not_free_to_play(self):
        raw = payload()
        raw["10"]["data"]["price_overview"] = {"currency": "EUR", "final": 0}
        game = fixture(raw)
        self.assertIsNone(game.price)
        self.assertFalse(satisfies(game, Filters(free_only=True), set()))
        raw["10"]["data"]["is_free"] = True
        self.assertEqual(fixture(raw).price.amount_cents, 0)

    def test_identity_and_content_are_conservative(self):
        raw = payload()
        raw["10"]["data"]["steam_appid"] = 11
        with self.assertRaises(ValueError):
            fixture(raw)
        for patch, expected in (({"type": "dlc"}, "excluded"), ({"content_descriptors": {"ids": [3]}}, "excluded"),
                                ({"release_date": {}}, "quarantined")):
            raw = payload()
            raw["10"]["data"].update(patch)
            self.assertEqual(fixture(raw).eligibility, expected)

    def test_prices_do_not_change_semantic_hash(self):
        raw = payload()
        changed = copy.deepcopy(raw)
        changed["10"]["data"]["price_overview"]["final"] = 2999
        self.assertEqual(fixture(raw).semantic_hash, fixture(changed).semantic_hash)
        self.assertEqual(fixture().description, "A combat game.")

    def test_all_template_citations_resolve_and_no_subjective_claims(self):
        game = fixture()
        result = recommendation(game, [game], Filters(platforms=["windows"], required_modes=["single-player"], max_price_cents=2000))
        evidence_ids = {item.id for item in game.evidence}
        self.assertTrue(all(set(reason.evidence_ids).issubset(evidence_ids) for reason in result.reasons))
        self.assertNotIn("less repetition", result.model_dump_json())

    def test_artifact_snapshot_tampering_is_rejected(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            body = json.dumps(payload()).encode()
            (directory / "10.json").write_bytes(body)
            source = Source(url="https://store.steampowered.com/api/appdetails?appids=10&cc=us", collected_at=datetime.now(UTC), sha256=hashlib.sha256(body).hexdigest())
            write_json(directory / "collection.json", {"app_ids": [10], "observations": [{"app_id": 10, "snapshot": "10.json", "source": source.model_dump(mode="json")}]})
            self.assertEqual(normalize(directory)["games"], 1)
            (directory / "10.json").write_bytes(b"{}")
            with self.assertRaises(ValueError):
                normalize(directory)

    def test_vectors_and_bounded_input_are_checked(self):
        with self.assertRaises(ValidationError):
            Embedding(app_id=10, semantic_hash="a" * 64, vector=[0.0] * 384)
        with TestClient(create_app(Settings())) as client:
            invalid = client.post("/api/v1/discover", json={"favorite_ids": [-1], "secret": "do-not-echo"})
            self.assertEqual(invalid.status_code, 422)
            self.assertNotIn("do-not-echo", invalid.text)
            self.assertEqual(client.post("/api/v1/discover", json={}).json()["code"], "database_unconfigured")
            self.assertEqual(client.get("/api/v1/games/2147483648").status_code, 422)
            self.assertEqual(client.get("/api/v1/games/-1").status_code, 422)
            preflight = client.options("/api/v1/discover", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
            self.assertEqual(preflight.status_code, 200)
