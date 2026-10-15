"""Explicit opt-in real API/database M2 smoke, with no inference provider calls."""

import time
from pathlib import Path

from fastapi.testclient import TestClient

from game_discovery.api.main import create_app
from game_discovery.catalog.contracts import Filters, Game
from game_discovery.catalog.discovery import satisfies
from game_discovery.core.settings import Settings
from game_discovery.jobs.catalog import write_json


def verify_catalog(output: Path) -> dict:
    measurements = []
    examples = []
    with TestClient(create_app(Settings.from_environment())) as client:
        status = client.get("/api/v1/catalog/status")
        assert status.status_code == 200 and status.json()["state"] == "ready", "Active catalog required"
        assert client.get("/health/ready").status_code == 200
        page = client.get("/api/v1/games", params={"q": "Hades"}).json()
        assert any(game["app_id"] == 1145360 for game in page["items"]), "Hades seed missing"
        assert client.get("/api/v1/games/1145360").status_code == 200
        assert client.get("/api/v1/games/2147483647").status_code == 404
        resolved = client.post("/api/v1/games/resolve", json={"app_ids": [1145360, 2147483647]}).json()
        assert resolved["unknown_ids"] == [2147483647]
        assert client.get("/api/v1/facets").status_code == 200
        cases = [Filters(), Filters(max_price_cents=2000, price_operator="lt", platforms=["windows"], required_modes=["single-player"]),
                 Filters(free_only=True), Filters(platforms=["mac", "linux"], platform_match="all"),
                 Filters(required_modes=["online-co-op"]), Filters(required_modes=["local-co-op"]),
                 Filters(max_price_cents=0, price_operator="lt"), Filters(unwanted_terms=["action"])]
        initial = client.post("/api/v1/discover", json={"favorite_ids": [1145360]}).json()
        assert initial["results"], "Seed discovery must return useful candidates"
        cases.append(Filters(excluded_ids=[item["game"]["app_id"] for item in initial["results"]]))
        for filters in cases:
            started = time.perf_counter()
            response = client.post("/api/v1/discover", json={"favorite_ids": [1145360], "filters": filters.model_dump(), "limit": 10})
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            assert response.status_code == 200, "Discovery returned an error"
            body = response.json()
            assert body["effective_criteria"] == filters.model_dump(), "Filters changed unexpectedly"
            for item in body["results"]:
                game = Game.model_validate(item["game"])
                assert satisfies(game, filters, set([1145360] + filters.excluded_ids)), "Constraint violation"
                assert all(set(reason["evidence_ids"]).issubset({e.id for e in game.evidence}) for reason in item["reasons"])
            if filters.max_price_cents == 0 and filters.price_operator == "lt":
                assert body["results"] == [] and body["suggested_refinements"], "Impossible budget was relaxed"
            examples.append({"filters": filters.model_dump(), "result_ids": [item["game"]["app_id"] for item in body["results"]]})
            measurements.append(elapsed)
        assert client.post("/api/v1/discover", json={"favorite_ids": [2147483647]}).status_code == 422
        preflight = client.options("/api/v1/discover", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
        assert preflight.status_code == 200
    result = {"status": "passed", "catalog": status.json(), "cases": examples,
              "request_ms": measurements, "sample_size": len(measurements),
              "scope": "Local FastAPI TestClient to real restricted PostgreSQL login; not public HTTP or relevance evaluation."}
    write_json(output, result)
    return result
