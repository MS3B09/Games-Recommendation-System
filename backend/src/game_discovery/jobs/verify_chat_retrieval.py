"""R1 read-only acceptance probe using ACTUAL application query settings.

Run directly as a module. No provider imports/calls, migrations, downloads,
quota reservations or database writes. The JSON contains curated queries/IDs,
not secrets, driver errors or real user conversations.
"""

import argparse
import hashlib
import json
import math
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from game_discovery.catalog.contracts import MODEL_ID, MODEL_REVISION, DiscoverRequest, Filters, digest
from game_discovery.catalog.discovery import satisfies
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.jobs.encoder_parity import PARITY_TEXTS, MemorySampler
from game_discovery.retrieval.chat import ChatRetriever, RANKING_VERSION
from game_discovery.retrieval.query import BoundedQueryEncoder, load_query_encoder

REFERENCE_SHA256 = "238406a24e756aa17578f3584e0cd4b20f2839447a1d6071e2e0dbd432a29530"


def verify(output: Path, reference_path: Path, repetitions: int) -> int:
    import numpy as np

    result = {"schema_version": 1, "measured_at": datetime.now(UTC).isoformat(), "status": "in_progress",
              "phase": "configuration", "checks": [], "live_provider_calls": 0, "database_writes": 0,
              "ranking_version": RANKING_VERSION}
    engine = None

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        result["checks"].append(name)

    try:
        with MemorySampler() as memory:
            settings = Settings.from_environment()
            configured = {key: bool(getattr(settings, key)) for key in
                          ("query_tokenizer_path", "query_model_path", "query_artifact_path")}
            result["configuration"] = {"query_paths_configured": configured,
                                       "database_configured": bool(settings.database_url.get_secret_value())}
            check("all_actual_query_settings_present", all(configured.values()))
            started = time.perf_counter()
            encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path,
                                         settings.query_artifact_path)
            check("actual_encoder_loaded_with_hash_manifest_checks", encoder is not None)
            result["encoder_load_ms"] = (time.perf_counter() - started) * 1000
            result["phase"] = "parity"
            body = reference_path.read_bytes()
            check("retained_cpu_reference_hash_matches_r0", hashlib.sha256(body).hexdigest() == REFERENCE_SHA256)
            reference = json.loads(body)
            check("reference_model_and_revision_match", (reference["model"], reference["revision"]) == (MODEL_ID, MODEL_REVISION))
            expected = np.array(reference["vectors"], dtype=np.float32)
            # Sequential one-text calls use the same bounded serving encoder.
            actual = np.array([encoder(query) for query in PARITY_TEXTS], dtype=np.float32)
            check("sixteen_fixed_reference_vectors", expected.shape == actual.shape == (16, 384))
            cosine = np.sum(actual * expected, axis=1)
            error = float(np.max(np.abs(actual - expected)))
            check("fresh_float_onnx_cpu_parity", float(cosine.min()) >= 0.9999 and error <= 0.0001)
            result["parity"] = {"texts": 16, "texts_sha256": digest(PARITY_TEXTS),
                "reference_sha256": REFERENCE_SHA256, "model_id": MODEL_ID, "model_revision": MODEL_REVISION,
                "minimum_cosine": float(cosine.min()), "max_absolute_component_error": error,
                "reference_regenerated": False, "model_downloads": 0}

            result["phase"] = "catalog"
            engine = create_runtime_engine(settings.database_url)
            check("runtime_database_configured", engine is not None)
            repository = CatalogRepository(engine)
            page = repository.search("", 256, 0)
            check("complete_bounded_catalog_inventory", 0 < page.total == len(page.items) <= 256)
            check("active_version_matches_configured_encoder", page.catalog_version == encoder.catalog_version)
            result["catalog"] = {"version": page.catalog_version, "eligible_games": page.total}
            retriever = ChatRetriever(repository, encoder)
            main_request = DiscoverRequest(favorite_ids=[1145360], filters=Filters(platforms=["windows"], max_price_cents=2000), limit=4)
            main_before = repository.discover(main_request)

            result["phase"] = "titles"
            title_results = []
            for query in ("spiderman", "Spider-Man", "spider man remastered", "Marvel's Spider-Man Remastered",
                          "Marvel’s Spider-Man Remastered"):
                reply = retriever.lookup_title(query)
                check("title_variant_" + query, reply.outcome.kind == "found" and reply.outcome.evidence_ids == [1817070])
                check("title_lookup_records_single_player_" + query, reply.candidates[0].game.modes == ["single-player"])
                title_results.append({"query": query, "outcome": reply.outcome.model_dump()})
            ambiguous = retriever.lookup_title("ori")
            check("real_catalog_franchise_ambiguity", ambiguous.outcome.kind == "ambiguous"
                  and set(ambiguous.outcome.evidence_ids) == {261570, 387290})
            absent = retriever.lookup_title("R1 nonexistent zephyr clockwork title 987654")
            check("catalog_absence_requires_completed_title_search", absent.outcome.kind == "not_in_catalog"
                  and absent.outcome.title_search_complete and absent.outcome.channels == ["title"])
            result["titles"] = title_results + [{"query": "ori", "outcome": ambiguous.outcome.model_dump()},
                {"query": "R1 nonexistent zephyr clockwork title 987654", "outcome": absent.outcome.model_dump()}]

            result["phase"] = "candidates"
            query = "combat exploration"
            vector = encoder(query)
            # Independent bounded vector inventory to check exact eligible top-20
            # against Python cosine, not just assert our SQL contains predicates.
            with repository.snapshot() as (connection, version):
                rows = connection.execute(text("""select app_id,cast(embedding as text)
                    from discovery.game_embeddings where version=:v order by app_id limit 257"""), {"v": version})
                stored = {row[0]: json.loads(row[1]) for row in rows}
            check("vector_inventory_matches_active_version", version == page.catalog_version and len(stored) <= 256)

            def similarity(app_id):
                item = stored[app_id]
                return sum(x * y for x, y in zip(vector, item, strict=True)) / math.sqrt(
                    sum(x * x for x in vector) * sum(y * y for y in item))

            filter_cases = [
                ("neutral", Filters()),
                ("inclusive_price", Filters(max_price_cents=1999)),
                ("strict_price", Filters(max_price_cents=1999, price_operator="lt")),
                ("minimum_and_maximum", Filters(min_price_cents=1000, max_price_cents=2000)),
                ("free_only", Filters(free_only=True, min_price_cents=0, max_price_cents=0)),
                ("platform_any", Filters(platforms=["windows", "linux"])),
                ("platform_all", Filters(platforms=["windows", "linux"], platform_match="all")),
                ("all_modes", Filters(required_modes=["single-player", "online-co-op"])),
                ("all_genres", Filters(required_genres=["action", "adventure"])),
                ("unwanted", Filters(unwanted_terms=["action"])),
                ("excluded", Filters(excluded_ids=[item.app_id for item in page.items[:10]])),
                ("impossible", Filters(min_price_cents=999999, max_price_cents=1000000)),
            ]
            filter_results = []
            for name, filters in filter_cases:
                reply = retriever.recommend(query, filters)
                eligible = [game for game in page.items if game.app_id in stored
                            and satisfies(game, filters, set(filters.excluded_ids))]
                expected_ids = [game.app_id for game in sorted(eligible, key=lambda game: (-similarity(game.app_id), game.app_id))[:20]]
                check("semantic_filtered_top20_" + name, list(reply.semantic_ids) == expected_ids)
                check("semantic_capability_" + name, reply.outcome.semantic_available and "semantic" in reply.outcome.channels)
                canonical = {game.app_id: game for game in page.items}
                check("every_lexical_id_obeys_hard_conditions_" + name,
                      all(satisfies(canonical[app_id], filters, set(filters.excluded_ids)) for app_id in reply.lexical_ids))
                check("pool_and_evidence_bounds_" + name, len(reply.lexical_ids) <= 20 and len(reply.semantic_ids) <= 20
                      and len(reply.candidates) <= 8 and len(reply.fused_ranks) <= 40)
                filter_results.append({"name": name, "filters": filters.model_dump(), "outcome": reply.outcome.model_dump(),
                    "lexical_ids": reply.lexical_ids, "semantic_ids": reply.semantic_ids, "fused_ranks": reply.fused_ranks})
            result["filter_cases"] = filter_results
            check("impossible_filters_are_not_catalog_absence", reply.outcome.kind == "no_recommendation_match")

            fallback = ChatRetriever(repository, None).recommend("r1zzzxxyyunknownword")
            check("real_lexical_no_match_has_no_zero_score_fillers", fallback.lexical_ids == () and fallback.candidates == ())
            check("missing_encoder_is_not_semantic_success", fallback.outcome.degraded_reason == "encoder_missing"
                  and not fallback.outcome.semantic_available and fallback.outcome.kind == "no_recommendation_match")
            old_encoder = BoundedQueryEncoder(lambda _: vector, "deliberately-stale-r1-version")
            mismatch = ChatRetriever(repository, old_encoder).recommend(query)
            check("active_version_mismatch_is_truthful_lexical_fallback", mismatch.outcome.degraded_reason == "artifact_mismatch"
                  and not mismatch.outcome.semantic_available and not mismatch.semantic_ids)
            result["fallbacks"] = {"missing": fallback.outcome.model_dump(), "mismatch": mismatch.outcome.model_dump()}

            # A development example, NOT held-out relevance scoring or a new
            # semantic cutoff. Candidate scores are not probabilities of fit.
            development = retriever.recommend("tending a farm and getting to know a small town")
            check("development_farm_anchor_in_evidence", 413150 in development.outcome.evidence_ids)
            result["development_example"] = {"query": "tending a farm and getting to know a small town",
                "evidence_ids": development.outcome.evidence_ids,
                "ranks": [asdict(item) | {"game": {"app_id": item.game.app_id, "title": item.game.title}}
                          for item in development.candidates]}

            result["phase"] = "timings"
            timings = []
            encoding = []
            for _ in range(repetitions):
                started = time.perf_counter()
                encoder(query)
                encoding.append((time.perf_counter() - started) * 1000)
                started = time.perf_counter()
                retriever.recommend(query, Filters(platforms=["windows"], max_price_cents=2000))
                timings.append((time.perf_counter() - started) * 1000)
            result["timings"] = {"warm_samples": repetitions,
                "encoding_only_median_ms": float(np.percentile(encoding, 50)),
                "encoding_only_p95_ms": float(np.percentile(encoding, 95)),
                "encoding_plus_remote_retrieval_median_ms": float(np.percentile(timings, 50)),
                "encoding_plus_remote_retrieval_p95_ms": float(np.percentile(timings, 95)),
                "local_warm_target_ms": 1000}
            check("main_discover_results_unchanged_by_chat_reads", repository.discover(main_request) == main_before)
            result["main_discovery_ids_before_and_after"] = [item.game.app_id for item in main_before[1]]
            result["peak_interpreter_rss_mib"] = memory.peak / 1024**2
            result["status"] = "ok"
            result["phase"] = "complete"
    except Exception as error:
        result["status"] = "failed"
        result["error_type"] = type(error).__name__
        if isinstance(error, AssertionError):
            # Only locally authored gate labels, never driver/native messages.
            result["failed_gate"] = str(error)
    finally:
        if engine is not None:
            engine.dispose()
    output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "phase": result["phase"], "checks": len(result["checks"]),
                      "failed_gate": result.get("failed_gate"), "report": str(output), "provider_calls": 0}))
    return 0 if result["status"] == "ok" else 1


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=root / "data/reports/offline-reference.json")
    parser.add_argument("--repetitions", type=int, default=12, choices=range(1, 31))
    args = parser.parse_args()
    if not args.output.parent.is_dir():
        parser.error("Output parent must already exist")
    return verify(args.output, args.reference, args.repetitions)


if __name__ == "__main__":
    raise SystemExit(main())
