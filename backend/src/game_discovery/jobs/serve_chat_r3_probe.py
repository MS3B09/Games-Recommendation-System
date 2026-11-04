"""Developer-only loopback R3 browser probe. Actual read-only catalog/encoder;
scripted Groq HTTP and budget. No live provider calls or quota reservations.
"""

import argparse
import json
import os
from unittest.mock import MagicMock, patch


def main() -> None:
    import uvicorn

    from game_discovery.ai.provider import AIFailure, GroqAssistant
    from game_discovery.catalog.repository import CatalogRepository
    from game_discovery.core.settings import Settings
    from game_discovery.db.engine import create_runtime_engine
    from game_discovery.retrieval.query import load_query_encoder

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, choices=[8002], default=8002)
    args = parser.parse_args()
    settings = Settings.from_environment()
    with patch.dict(os.environ, {"GAME_DISCOVERY_ENV_FILE": os.devnull}):
        from game_discovery.api.main import create_app
    encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
    if encoder is None:
        raise SystemExit("The R3 probe requires the configured pinned encoder")
    engine = create_runtime_engine(settings.database_url)
    budget = MagicMock()
    budget.reserve.return_value = True
    model = GroqAssistant(settings, budget)
    plans = {
        "Find multiplayer games": {"kind": "recommend", "query": "multiplayer cooperative exploration",
            "criteria_patch": [{"scope": "conversation", "set": {"required_modes": ["multiplayer"]}}]},
        "Does a spiderman game exist?": {"kind": "title_lookup", "title_mentions": ["spiderman"]},
        "Would it meet those requirements?": {"kind": "game_facts", "reference": "last_game", "evaluate_prior_requirements": True},
        "More multiplayer options": {"kind": "recommend", "query": "multiplayer cooperative exploration"},
        "I played Spider-Man": {"kind": "recommend", "query": "multiplayer cooperative exploration",
            "exclusion_patch": [{"action": "add", "target": {"title": "spiderman"}}]},
        "Include Spider-Man again": {"kind": "recommend", "query": "multiplayer cooperative exploration",
            "exclusion_patch": [{"action": "remove", "target": {"title": "spiderman"}}]},
    }
    stats = {"mock_http_calls": 0, "bounded_packets": True, "matched_reservations": True,
        "live_provider_calls": 0, "actual_quota_reservations": 0, "database_writes": 0,
        "encoder_loaded": True, "semantic_candidate_queries": 0}

    def transport(request, **kwargs):
        payload = json.loads(request.data)
        packet = json.loads(payload["messages"][-1]["content"])
        size = len(json.dumps(payload["messages"], ensure_ascii=False).encode())
        stats["mock_http_calls"] += 1
        stats["bounded_packets"] &= size <= 12000 and kwargs["timeout"] == 3
        stats["matched_reservations"] &= budget.reserve.call_args.args[0] == size + 1280
        if "message" in packet:
            output = plans.get(packet["message"])
            if output is None:
                raise AIFailure("This developer probe accepts only its scripted test messages")
        else:
            output = {"message": "Inspect these recorded catalog facts; subjective fit is unverified.",
                "game_ids": [game["app_id"] for game in packet["games"][:2]], "claims": {"claims": []}}
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"choices": [{"message": {"content": json.dumps(output)}}]}).encode()
        return response

    safe = settings.model_copy(update={"ai_enabled": False, "allowed_origins": ("http://127.0.0.1:4173",)})
    repo = CatalogRepository(engine)
    candidates = repo.chat_candidates

    def observe_candidates(*args, **kwargs):
        result = candidates(*args, **kwargs)
        if result.semantic_used:
            stats["semantic_candidate_queries"] += 1
        return result

    app = create_app(safe, repository=repo, query_encoder=encoder, chat_model=model)

    @app.get("/__r3_probe", include_in_schema=False)
    def probe_stats() -> dict:
        return {**stats, "mock_reservations": budget.reserve.call_count}

    try:
        with (patch("game_discovery.ai.provider.urlopen", side_effect=transport),
              patch.object(repo, "chat_candidates", side_effect=observe_candidates)):
            uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1, access_log=False, log_level="error")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
