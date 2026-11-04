"""Fixed three-pass runtime-only R4 latency benchmark; no inference/reservations.

No per-turn journal writes inside the measured sequence. Every held-out real
turn is included, including slow/error observations. Ranking/fixtures unchanged.
"""

import argparse
import gc
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.ai.chat_contracts import ChatStateV2, ChatTurn
from game_discovery.ai.rag import StageTimings
from game_discovery.catalog.contracts import ConversationMessage
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.jobs.chat_evaluation import METHODS, POLICY, OracleModel, RecordedRAG, SemanticBaseline, load_cases, oracle_plan, percentile
from game_discovery.jobs.continue_chat_evaluation import identity
from game_discovery.jobs.encoder_parity import MemorySampler
from game_discovery.jobs.evaluate_chat import TimedEncoder, save
from game_discovery.retrieval.query import load_query_encoder

REPETITIONS = 3


def run(output):
    if output.exists() or not output.parent.is_dir():
        raise ValueError("new_output_in_existing_parent_required")
    report = identity("held_out")
    report.update(mode="runtime_latency_only", repetitions=REPETITIONS,
                  protocol="Three fixed full passes; alternate method order per case/pass; no per-turn disk writes; no inference; no retries; include slow/error observations.",
                  records=[], status="in_progress")
    save(output, report)  # Protocol persisted before first timed observation.
    settings = Settings.from_environment()
    encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
    engine = create_runtime_engine(settings.database_url)
    if encoder is None or engine is None:
        raise ValueError("configured_encoder_and_database_required")
    encoder = TimedEncoder(encoder)
    repository = CatalogRepository(engine)
    page = repository.search("", 256, 0)
    if page.total != 40 or page.catalog_version != encoder.catalog_version:
        raise ValueError("catalog_encoder_mismatch")
    games = {g.app_id: g for g in page.items}
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    cases = [c for c in load_cases() if c["split"] == "held_out" and c["source"] == "real_catalog"]
    try:
        with MemorySampler() as memory:
            for repetition in range(REPETITIONS):
                cold = set(METHODS)
                for number, case in enumerate(cases):
                    for method in METHODS if (number + repetition) % 2 == 0 else tuple(reversed(METHODS)):
                        state, messages = ChatStateV2(), []
                        for index, turn in enumerate(case["turns"]):
                            model = OracleModel(oracle_plan(case, index, games, policy))
                            rag = (RecordedRAG if method == "proposed" else SemanticBaseline)(model, repository, encoder)
                            observer = StageTimings()
                            before = len(encoder.samples)
                            item = {"pass": repetition + 1, "case_id": case["id"], "turn": index + 1,
                                    "method": method, "warm": method not in cold}
                            cold.discard(method)
                            started = time.perf_counter()
                            try:
                                result = rag.invoke(ChatTurn(message=turn["user"], messages=messages, state=state), observer)
                                item.update(status="ok", ranked_ids=result.retrieval.evidence_ids if result.retrieval else [])
                                state = result.state
                                messages = [*messages, ConversationMessage(role="user", content=turn["user"]),
                                            ConversationMessage(role="assistant", content=result.message)][-20:]
                                while sum(len(m.content) for m in messages) > 12000:
                                    messages.pop(0)
                            except Exception as error:
                                item.update(status="failed", error_type=type(error).__name__)
                            finally:
                                item.update(total_ms=(time.perf_counter() - started) * 1000,
                                            stage_ms=observer.timings_ms, encoding_ms=encoder.samples[before:])
                                report["records"].append(item)
                            del rag
                            gc.collect()
                            if item["status"] == "failed":
                                break
                # Only between whole fixed passes, outside measured sequences.
                save(output, report)
            report["peak_sampled_rss_mib"] = memory.peak / 1024**2
        report["summary"] = {}
        for method in METHODS:
            rows = [r for r in report["records"] if r["method"] == method and r["warm"]]
            report["summary"][method] = {
                "warm_samples": len(rows), "failed_samples": sum(r["status"] != "ok" for r in rows),
                "retrieve_p95_ms": percentile([r["stage_ms"].get("retrieve", 0) for r in rows]),
                "per_pass_retrieve_p95_ms": [percentile([r["stage_ms"].get("retrieve", 0) for r in rows
                                                         if r["pass"] == n]) for n in range(1, REPETITIONS + 1)]}
        report.update(status="completed", finished_at=datetime.now(UTC).isoformat())
        save(output, report)
        print(json.dumps(report["summary"]))
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output)


if __name__ == "__main__":
    main()
