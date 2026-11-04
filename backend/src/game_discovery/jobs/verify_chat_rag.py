"""Read-only R2 integration probe: actual catalog/encoder, MOCKED HTTP + budget.

Not held-out evaluation or a live-model quality check. No provider call, quota
reservation, database write, model download, tracing or browser work is performed.
"""

import argparse
import importlib.metadata
import json
import math
import os
import platform
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch


def run(repetitions: int) -> dict:
    import psutil
    from game_discovery.jobs.encoder_parity import MemorySampler

    checks: list[str] = []
    def check(name: str, condition: bool) -> None:
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    with MemorySampler() as memory:
        started = time.perf_counter()
        from game_discovery.ai.chat_contracts import ChatStateV2, ChatTurn
        from game_discovery.ai.chat_memory import legacy_state
        from game_discovery.ai.provider import AIFailure, GroqAssistant
        from game_discovery.ai.rag import ConversationalRAG, StageTimings
        from game_discovery.catalog.contracts import DiscoverRequest, Filters
        from game_discovery.catalog.discovery import satisfies
        from game_discovery.catalog.repository import CatalogRepository
        from game_discovery.core.settings import Settings
        from game_discovery.db.engine import create_runtime_engine
        from game_discovery.retrieval.query import load_query_encoder
        core_domain_import_ms = (time.perf_counter() - started) * 1000
        settings = Settings.from_environment()
        # Prevent an unnecessary second model/engine from module-level app while
        # retaining actual settings already captured above. No env file is edited.
        with patch.dict(os.environ, {"GAME_DISCOVERY_ENV_FILE": os.devnull}):
            from game_discovery.api.main import create_app
        from fastapi.testclient import TestClient

        started = time.perf_counter()
        encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
        check("actual_pinned_encoder_loaded", encoder is not None)
        encoder_load_ms = (time.perf_counter() - started) * 1000
        engine = create_runtime_engine(settings.database_url)
        repo = CatalogRepository(engine)
        budget = MagicMock()
        budget.reserve.return_value = True
        model = GroqAssistant(settings, budget)
        started = time.perf_counter()
        rag = ConversationalRAG(model, repo, encoder)
        graph_build_ms = (time.perf_counter() - started) * 1000
        plan: dict = {}
        reject_candidates = False
        requests: list[dict] = []
        turn_records: list[dict] = []

        def transport(request, **kwargs):
            payload = json.loads(request.data)
            packet = json.loads(payload["messages"][-1]["content"])
            from game_discovery.ai.chat_evidence import GENERATE, INTERPRET, input_bytes
            stage = "interpret" if "message" in packet else "generate"
            size = input_bytes(INTERPRET if stage == "interpret" else GENERATE, packet)
            check("bounded_" + stage + "_request_" + str(len(requests)), size <= 12000)
            check("reservation_matches_request_" + str(len(requests)), budget.reserve.call_args.args[0] == size + 1280)
            check("transport_bounds_" + str(len(requests)), kwargs["timeout"] == 3 and
                  payload["max_completion_tokens"] == 1024 and payload["stream"] is False)
            requests.append({"stage": stage, "input_json_bytes": size, "mock_reserved_tokens": size + 1280})
            output = plan if stage == "interpret" else {
                "message": "Inspect the recorded catalog facts on the cards; subjective fit remains unverified.",
                "game_ids": [] if reject_candidates else [g["app_id"] for g in packet["games"][:2]],
                "claims": {"claims": []}}
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps({"choices": [
                {"message": {"content": json.dumps(output)}}]}).encode()
            return response

        def turn(name, next_plan, state=None, message=None):
            nonlocal plan
            plan = next_plan
            before = len(requests)
            observer = StageTimings()
            started = time.perf_counter()
            response = rag.invoke(ChatTurn(message=message or name, state=state or ChatStateV2()), observer)
            elapsed = (time.perf_counter() - started) * 1000
            count = len(requests) - before
            check(name + "_at_most_two_calls", count <= 2)
            check(name + "_complete_stage_timings", set(observer.timings_ms) ==
                  {"interpret", "remember", "retrieve", "evidence", "generate", "validate"})
            for card in response.games:
                canonical = repo.resolve([card.game.app_id]).items[0]
                check(name + "_canonical_card_" + str(card.game.app_id), card.game == canonical)
            turn_records.append({"name": name, "mock_calls": count, "duration_ms": round(elapsed, 3),
                "stages_ms": observer.timings_ms, "selected_ids": [c.game.app_id for c in response.games],
                "outcome": response.retrieval.model_dump() if response.retrieval else None})
            return response

        try:
            main_request = DiscoverRequest(favorite_ids=[1145360], filters=Filters(
                max_price_cents=2000, platforms=["windows"], required_modes=["single-player"]), limit=4)
            before_main = repo.discover(main_request)
            with patch("game_discovery.ai.provider.urlopen", side_effect=transport):
                hello = turn("greeting", {"kind": "social", "reply": "Hello! What would you enjoy playing?"})
                check("greeting_no_games_or_retrieval", not hello.games and hello.retrieval is None)
                first = turn("multiplayer", {"kind": "recommend", "query": "multiplayer cooperative exploration", "criteria_patch": [
                    {"scope": "conversation", "set": {"required_modes": ["multiplayer"]}}]})
                check("multiplayer_semantic_used", first.retrieval.semantic_available and "semantic" in first.retrieval.channels)
                check("multiplayer_cards_pass", bool(first.games) and all("multiplayer" in c.game.modes for c in first.games))
                state = first.state
                for index, title in enumerate(("spiderman", "spider man", "spider-man", "Marvel's Spider-Man Remastered")):
                    facts = turn("spider_variant_" + str(index), {"kind": "title_lookup", "title_mentions": [title]}, state)
                    check("spider_identity_" + str(index), [c.game.app_id for c in facts.games] == [1817070])
                    check("spider_mismatch_" + str(index), facts.retrieval.kind == "found_but_mismatch" and
                          "single-player" in facts.message and "multiplayer" in facts.message)
                    check("spider_memory_" + str(index), facts.state.criteria == first.state.criteria and
                          facts.state.query == first.state.query and facts.state.provenance == first.state.provenance)
                    state = facts.state
                suitability = turn("explicit_suitability", {"kind": "game_facts", "reference": "last_game",
                                   "evaluate_prior_requirements": True}, state)
                check("suitability_mismatch", suitability.retrieval.kind == "found_but_mismatch")
                more = turn("more_multiplayer", {"kind": "recommend", "query": "more multiplayer cooperative exploration"}, suitability.state)
                check("multiplayer_retained_after_facts", bool(more.games) and all("multiplayer" in c.game.modes for c in more.games))
                excluded_id = more.games[0].game.app_id
                excluded_title = more.games[0].game.title
                played = turn("played_position", {"kind": "recommend", "query": "multiplayer cooperative exploration",
                    "exclusion_patch": [{"action": "add", "target": {"shown_position": 1}}]}, more.state)
                check("played_exclusion_canonical", excluded_id in [e.app_id for e in played.state.exclusions] and
                      excluded_id not in [c.game.app_id for c in played.games])
                inspect_played = turn("played_still_inspectable", {"kind": "game_facts", "title_mentions": [excluded_title]}, played.state)
                check("excluded_fact_visible", [c.game.app_id for c in inspect_played.games] == [excluded_id] and
                      inspect_played.retrieval.kind == "found_but_mismatch")
                undo = turn("undo_exclusion", {"kind": "recommend", "query": "multiplayer cooperative exploration",
                    "exclusion_patch": [{"action": "remove", "target": {"title": excluded_title}}]}, inspect_played.state)
                check("undo_only_chat_exclusion", not undo.state.exclusions)
                limited = turn("one_turn_price_platform", {"kind": "recommend", "query": "multiplayer cooperative exploration",
                    "criteria_patch": [{"scope": "turn", "set": {"max_price_cents": 2000, "platforms": ["windows"]}}]}, undo.state)
                check("turn_conditions_not_persisted", limited.state.criteria == undo.state.criteria)
                check("turn_conditions_enforced", all(satisfies(c.game, Filters(max_price_cents=2000,
                    platforms=["windows"], required_modes=["multiplayer"]), set()) for c in limited.games))
                ambiguous = turn("ori_ambiguity", {"kind": "title_lookup", "title_mentions": ["Ori"]}, first.state)
                check("ori_options_and_unchanged_state", ambiguous.retrieval.kind == "ambiguous" and
                      set(ambiguous.retrieval.evidence_ids) == {261570, 387290} and ambiguous.state == first.state)
                absent = turn("absent_title", {"kind": "title_lookup", "title_mentions": ["Unreal Catalog Zzzzz 987654"]})
                check("absence_is_catalog_only", absent.retrieval.kind == "not_in_catalog" and
                      absent.retrieval.title_search_complete and "elsewhere" in absent.message)
                compare = turn("comparison", {"kind": "compare", "title_mentions": ["spiderman", "Portal 2"]}, first.state)
                check("comparison_targets", compare.state.referenced_ids == [1817070, 620])
                legacy = legacy_state(Filters(max_price_cents=1, platforms=["linux"]), "legacy topic", [1817070], [1817070])
                old_facts = turn("legacy_fact", {"kind": "game_facts", "reference": "last_game"}, legacy)
                check("legacy_conditions_not_active", old_facts.retrieval.kind == "found" and bool(old_facts.games))
                old_recs = turn("legacy_recommendation_confirmation", {"kind": "recommend", "query": "combat"}, legacy)
                check("legacy_confirmation_preserves_state", old_recs.state == legacy and not old_recs.games)
                reject_candidates = True
                rejected = turn("unsupported_fit_no_selection", {"kind": "recommend", "query": "an unsupported subjective experience"})
                check("rejection_not_absence", rejected.retrieval.kind == "no_recommendation_match" and not rejected.games)
                reject_candidates = False
                budget.reserve.return_value = False
                count = len(requests)
                try:
                    turn("quota_denied", {"kind": "social", "reply": "Hello!"})
                except AIFailure as error:
                    check("quota_denied_without_http", str(error) == "ai_budget_unavailable" and len(requests) == count)
                else:
                    raise AssertionError("quota_not_enforced")
                budget.reserve.return_value = True
                plan = {"kind": "title_lookup", "title_mentions": ["spiderman"]}
                with TestClient(create_app(Settings(ai_enabled=False), repository=repo, query_encoder=encoder, chat_model=model)) as client:
                    reply = client.post("/api/v1/chat", json={"message": "Does spiderman exist?"})
                    check("existing_api_uses_new_title_path", reply.status_code == 200 and
                          reply.json()["games"][0]["game"]["app_id"] == 1817070)
                    check("api_preserves_legacy_state_shape", set(reply.json()["state"]) == {"criteria", "query", "excluded_ids", "shown_ids"})
                    limited_reply = client.post("/api/v1/chat", json={"message": "again"})
                    check("actual_api_throttle_retained", limited_reply.status_code == 429 and limited_reply.headers["retry-after"] == "30")
                warm = []
                overhead = []
                for index in range(repetitions):
                    turn("warm_" + str(index), {"kind": "recommend", "query": "multiplayer cooperative exploration"}, first.state)
                    record = turn_records[-1]
                    warm.append(record["duration_ms"])
                    overhead.append(max(0.0, record["duration_ms"] - sum(record["stages_ms"].values())))
            after_main = repo.discover(main_request)
            check("main_results_identical_before_after", before_main == after_main)
            check("all_provider_attempts_are_mocked_and_metered", budget.reserve.call_count == len(requests) + 1)
            info = psutil.Process().memory_info()
            peak = max(memory.peak, getattr(info, "peak_wset", info.rss))
            check("representative_probe_peak_below_400_mib", peak < 400 * 1024**2)
            def percentile(values):
                return sorted(values)[max(0, math.ceil(len(values) * .95) - 1)]
            return {"schema_version": 1, "status": "ok", "measured_at": datetime.now(UTC).isoformat(),
                "platform": platform.platform(), "python": platform.python_version(),
                "catalog_version": first.catalog_version, "encoder_catalog_version": encoder.catalog_version,
                "packages": {name: importlib.metadata.version(name) for name in
                    ("langchain-core", "langsmith", "langchain-protocol", "jsonpatch", "jsonpointer")},
                "checks": checks, "check_count": len(checks), "turns": turn_records,
                "mock_http_requests": requests, "mock_reservation_attempts": budget.reserve.call_count,
                "mock_denied_reservations": 1, "maximum_mock_reserved_tokens": max(r["mock_reserved_tokens"] for r in requests),
                "main_result_ids": [item.game.app_id for item in before_main[1]],
                "timing": {"fresh_process_core_domain_import_ms": core_domain_import_ms,
                    "encoder_load_ms": encoder_load_ms, "graph_build_ms": graph_build_ms,
                    "warm_samples": repetitions, "mocked_total_median_ms": statistics.median(warm),
                    "mocked_total_p95_ms": percentile(warm), "outside_stage_p95_ms": percentile(overhead),
                    "probe_peak_rss_mib": peak / 1024**2},
                "scope": "Actual restricted catalog/encoder and existing API; scripted provider JSON, HTTP and budget. No throttle bypass. Not answer quality or held-out evaluation.",
                "live_provider_calls": 0, "actual_quota_reservations": 0, "database_writes": 0,
                "browser_checks": False, "public_v2_integration": "Historical R2 scope; see separate R3 browser/API evidence"}
        finally:
            engine.dispose()


def main(default_output: Path | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=default_output is None, default=default_output)
    parser.add_argument("--repetitions", type=int, choices=range(1, 31), default=12)
    args = parser.parse_args()
    if not args.output.parent.is_dir():
        parser.error("The output parent directory must already exist")
    try:
        report = run(args.repetitions)
    except Exception as error:
        # Never print native SQL/connection/provider exception payloads.
        print(json.dumps({"status": "failed", "error_type": type(error).__name__,
                          "check": str(error) if isinstance(error, AssertionError) else "probe_failed"}))
        raise SystemExit(1) from None
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": report["check_count"], "timing": report["timing"],
                      "live_provider_calls": 0, "actual_quota_reservations": 0}))


if __name__ == "__main__":
    main()
