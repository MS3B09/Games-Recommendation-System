"""R4 reproducible retrieval comparison and separately approved live pilot.

offline: read-only catalog, oracle plans/scripted selections, no provider calls.
pilot: M01 development only, BOTH methods, durable 12-call/159360-token cap.
No automatic retries, downloads, quota resets or full held-out live execution.
"""

import argparse
import gc
import json
import os
import platform
import statistics
import sys
import time
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.ai.chat_contracts import ChatStateV2, ChatTurn
from game_discovery.ai.chat_evidence import input_bytes
from game_discovery.ai.provider import AIFailure, ClientThrottle, DatabaseBudget, GroqAssistant
from game_discovery.ai.rag import StageTimings
from game_discovery.catalog.contracts import MODEL_ID, MODEL_REVISION, ConversationMessage
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.jobs.chat_evaluation import (
    DATASET, MANIFEST, METHODS, PILOT_CALLS, PILOT_TOKENS, POLICY, ROOT,
    OracleModel, RecordedRAG, SemanticBaseline, load_cases, metrics, oracle_plan, percentile, sha256,
)
from game_discovery.jobs.encoder_parity import MemorySampler
from game_discovery.retrieval.query import load_query_encoder

PILOT_PATH = ROOT / "docs/reports/conversational-rag-r4-pilot.json"
RETEST_PATH = ROOT / "docs/reports/conversational-rag-r4-pilot-revision.json"
JOURNAL_INTERVALS = ContextVar("r4_journal_intervals", default=None)


def approval_limits(report):
    limits = report.get("approval_limits", {})
    return limits.get("max_calls", PILOT_CALLS), limits.get("max_reserved_tokens", PILOT_TOKENS)


def save(path, report):
    started = time.perf_counter()
    temporary = path.with_suffix(path.suffix + ".tmp")
    # Stream JSON instead of building a second whole-report Unicode buffer.
    with temporary.open("w", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    # Windows indexers can briefly hold the destination without delete sharing.
    # Retry only this atomic filesystem rename, NEVER inference/reservations.
    for index in range(5):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if index == 4:
                raise
            time.sleep(.05 * (index + 1))
    intervals = JOURNAL_INTERVALS.get()
    if intervals is not None:
        intervals.append((time.perf_counter() - started) * 1000)


class TimedEncoder:
    def __init__(self, encoder):
        self.encoder, self.catalog_version = encoder, encoder.catalog_version
        self.samples = []

    def __call__(self, query):
        started = time.perf_counter()
        try:
            return self.encoder(query)
        finally:
            self.samples.append((time.perf_counter() - started) * 1000)


def header(mode):
    return {"schema_version": 1, "mode": mode, "status": "in_progress",
        "started_at": datetime.now(UTC).isoformat(), "platform": platform.platform(), "python": platform.python_version(),
        "dataset_sha256": sha256(DATASET), "manifest_sha256": sha256(MANIFEST), "policy_sha256": sha256(POLICY),
        "evaluator_sha256": sha256(Path(__file__)),
        "adapter_sha256": sha256(Path(__file__).with_name("chat_evaluation.py")),
        "serving_source_sha256": {name: sha256(ROOT / "backend/src/game_discovery/ai" / name)
                                  for name in ("chat_evidence.py", "chat_memory.py", "rag.py", "provider.py")},
        "model_id": MODEL_ID, "model_revision": MODEL_REVISION, "methods": list(METHODS),
        "records": [], "provider_attempts": [], "live_provider_calls": 0, "actual_quota_reservations": 0,
        "synthetic_cases": "Not scored here; covered by separately recorded synthetic/backend/browser regressions.",
        "quality_gate": "incomplete: full held-out live comparison and human judgments not authorized/executed",
        "scope": "Oracle-intent retrieval/state only" if mode == "offline" else "Live M01 development pilot only"}


class CappedBudget:
    def __init__(self, delegate, report, path):
        self.delegate, self.report, self.path = delegate, report, path

    def reserve(self, tokens):
        attempts = self.report["provider_attempts"]
        # This attempt was journaled before entering the existing transport.
        max_calls, max_tokens = approval_limits(self.report)
        if len(attempts) > max_calls or sum(a["reserved_token_bound"] for a in attempts) > max_tokens:
            raise AIFailure("evaluation_approval_exhausted")
        attempt = attempts[-1]
        if tokens != attempt["reserved_token_bound"]:
            raise AIFailure("evaluation_accounting_mismatch")
        attempt["reservation"] = "pending"
        save(self.path, self.report)
        granted = self.delegate.reserve(tokens)
        attempt["reservation"] = "granted" if granted else "denied"
        self.report["actual_quota_reservations"] = sum(a.get("reservation") == "granted" for a in attempts)
        save(self.path, self.report)
        return granted


class JournalModel:
    def __init__(self, model, report, path):
        self.model, self.report, self.path = model, report, path
        self.context = {}

    def complete(self, instruction, data):
        amount = input_bytes(instruction, data) + 1280
        attempts = self.report["provider_attempts"]
        max_calls, max_tokens = approval_limits(self.report)
        if len(attempts) >= max_calls or sum(a["reserved_token_bound"] for a in attempts) + amount > max_tokens:
            raise AIFailure("evaluation_approval_exhausted")
        attempt = {**self.context, "stage": "interpret" if "message" in data else "generate",
                   "input_json_bytes": amount - 1280, "reserved_token_bound": amount,
                   "started_at": datetime.now(UTC).isoformat(), "status": "started", "reservation": "not_attempted"}
        attempts.append(attempt)
        save(self.path, self.report)
        started = time.perf_counter()
        try:
            value = self.model.complete(instruction, data)
            attempt["status"] = "returned_json"
            attempt["output"] = value
            return value
        except AIFailure as error:
            attempt["status"] = "failed"
            attempt["error_code"] = str(error)
            raise
        finally:
            usage = getattr(self.model, "last_usage", None)
            if isinstance(usage, dict):
                attempt["provider_usage"] = usage
            status = getattr(self.model, "last_http_status", None)
            if type(status) is int:
                attempt["http_status"] = status
            error_type = getattr(self.model, "last_error_type", None)
            if isinstance(error_type, str):
                attempt["transport_error_type"] = error_type
            attempt["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
            # A granted reservation authorizes one transport attempt, even if it
            # times out/returns invalid data. Never claim these calls are free.
            self.report["live_provider_calls"] = sum(a.get("reservation") == "granted" for a in attempts)
            save(self.path, self.report)


def record_turn(case, index, method, rag, model, state, messages, encoder, report, path):
    item = {"case_id": case["id"], "split": case["split"], "turn": index + 1, "method": method,
            "user": case["turns"][index]["user"], "status": "started",
            "started_at": datetime.now(UTC).isoformat()}
    report["records"].append(item)
    if report["mode"] != "offline":
        model.context = {k: item[k] for k in ("case_id", "turn", "method")} | {"revision": report["mode"]}
        report["last_turn_started_epoch"] = time.time()
    save(path, report)
    observer = StageTimings()
    encoding_before = len(encoder.samples)
    attempts_before = len(report["provider_attempts"])
    journal_intervals = []
    journal_token = JOURNAL_INTERVALS.set(journal_intervals)
    started = time.perf_counter()
    try:
        result = rag.invoke(ChatTurn(message=item["user"], state=state, messages=messages), observer)
        frame = rag.last_frame
        if result.catalog_version and result.catalog_version != report["catalog_version"]:
            raise ValueError("evaluation_catalog_changed")
        response = result.model_dump(mode="json", exclude={"games"})
        # Canonical facts/descriptions already live once in catalog_evidence.
        # Retain every answer/reason/tradeoff and selected ID without copying
        # full Game source/evidence documents into each repeated turn.
        response["games"] = [{"app_id": c.game.app_id, "reasons": [r.model_dump() for r in c.reasons],
                              "tradeoffs": c.tradeoffs} for c in result.games]
        item.update(status="ok", response=response,
            plan=frame.plan.model_dump(mode="json") if frame and frame.plan else None,
            metrics=metrics(case["turns"][index]["expect"], result, frame, frame.plan if frame else None),
            ranked_ids=[c.game.app_id for c in frame.retrieval.candidates] if frame and frame.retrieval else (
                result.retrieval.evidence_ids if result.retrieval else []),
            generation_evidence_ids=[d.metadata["app_id"] for d in frame.packet.documents] if frame and frame.packet else [],
            candidate_ranks=[{"app_id": c.game.app_id, "lexical_rank": c.lexical_rank,
                "semantic_rank": c.semantic_rank, "cosine_similarity": c.cosine_similarity, "rrf_score": c.rrf_score}
                for c in frame.retrieval.candidates] if frame and frame.retrieval else [])
        messages = [*messages, ConversationMessage(role="user", content=item["user"]),
                    ConversationMessage(role="assistant", content=result.message)][-20:]
        while sum(len(m.content) for m in messages) > 12000:
            messages.pop(0)
        return result.state, messages
    except Exception as error:
        item.update(status="failed", error_type=type(error).__name__)
        if isinstance(error, AIFailure):
            item["error_code"] = str(error)
        from pydantic import ValidationError
        if isinstance(error, ValidationError):
            item["validation_errors"] = [{"loc": list(e["loc"]), "type": e["type"]}
                                         for e in error.errors(include_input=False, include_context=False)]
        return None, messages
    finally:
        item["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
        JOURNAL_INTERVALS.reset(journal_token)
        item["journal_write_ms"] = round(sum(journal_intervals), 3)
        item["serving_equivalent_domain_ms"] = round(item["duration_ms"] - sum(journal_intervals), 3)
        item["latency_scope"] = "Domain invoke minus measured synchronous journal writes; real budget SQL retained; not browser/HTTP latency."
        item["stage_ms"] = observer.timings_ms
        item["encoding_ms"] = encoder.samples[encoding_before:]
        item["provider_attempts"] = len(report["provider_attempts"]) - attempts_before
        if report["mode"] != "offline":
            report["last_turn_completed_epoch"] = time.time()
        save(path, report)


def summarize(report):
    result = {}
    for method in METHODS:
        items = [r for r in report["records"] if r["method"] == method]
        good = [r for r in items if r["status"] == "ok"]
        values = [r["metrics"] for r in good]
        def rate(key):
            scored = [m[key] for m in values if m[key] is not None]
            return {"numerator": sum(scored), "denominator": len(scored),
                    "rate": sum(scored) / len(scored) if scored else None}
        warm = good[1:]
        result[method] = {"recorded_turns": len(items), "successful_turns": len(good),
            "failed_turns": len(items) - len(good), "target_hit_at_5": rate("target_hit_at_5"),
            "anchor_seed_hit_in_evidence": rate("anchor_seed_hit_in_evidence"),
            "outcome_match": rate("expected_outcome_match"),
            "hard_card_violations": sum(len(m["hard_card_violation_ids"]) for m in values),
            "forbidden_card_violations": sum(len(m["forbidden_card_ids_returned"]) for m in values),
            "failed_state_checks": sum(v is False for m in values for v in m["state_checks"].values()),
            "warm_success_samples": len(warm), "warm_total_median_ms": statistics.median([r["duration_ms"] for r in warm]) if warm else None,
             "warm_total_p95_ms": percentile([r["duration_ms"] for r in warm]),
             "warm_serving_equivalent_domain_p95_ms": percentile([r["serving_equivalent_domain_ms"] for r in warm
                                                                 if "serving_equivalent_domain_ms" in r]),
            "warm_retrieve_p95_ms": percentile([r["stage_ms"].get("retrieve", 0) for r in warm]),
            "encoding_p95_ms": percentile([v for r in good for v in r["encoding_ms"]]),
            "human_relevance": None, "unsupported_prose_claim_rate": None, "recall_at_8": None}
    return result


def run(args):
    cases = load_cases()
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    path = PILOT_PATH if args.mode == "pilot" else RETEST_PATH if args.mode == "retest" else args.output
    if not path.parent.is_dir():
        raise ValueError("output_parent_missing")
    report = header(args.mode)
    if args.mode != "offline" and path.exists():
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("status") in {"completed", "completed_with_failures"}:
            print(json.dumps({"status": "already_completed_no_calls", "mode": args.mode,
                              "recorded_aggregate_attempts": len(report["provider_attempts"])}))
            return
        current = header(args.mode)
        if any(report[k] != current[k] for k in ("mode", "dataset_sha256", "policy_sha256", "evaluator_sha256", "adapter_sha256", "serving_source_sha256")):
            raise ValueError("pilot_checkpoint_identity_mismatch")
        # Keep started/failed records as-is. They block that method's remaining
        # dependent turns and are never repeated during a restart.
    elif path.exists():
        raise ValueError("output_exists_use_a_new_path")
    if args.mode == "retest" and not path.exists():
        prior = json.loads(PILOT_PATH.read_text(encoding="utf-8"))
        if prior["status"] != "completed_with_failures" or prior["dataset_sha256"] != report["dataset_sha256"]:
            raise ValueError("initial_failed_pilot_required")
        report["prior_pilot_sha256"] = sha256(PILOT_PATH)
        report["provider_attempts"] = [a | {"revision": "initial"} for a in prior["provider_attempts"]]
        report["actual_quota_reservations"] = prior["actual_quota_reservations"]
        report["live_provider_calls"] = prior["live_provider_calls"]
        report["last_turn_completed_epoch"] = prior.get("last_turn_completed_epoch", prior.get("last_turn_started_epoch", 0))
        report["retest_approval"] = "Owner explicitly selected Fix and retest on 2026-10-25; only proposed M01 under the ORIGINAL aggregate 12-call/159360-token cap. Initial failures remain immutable in the original pilot artifact."
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock = lock_path.open("x", encoding="utf-8")
    engine = None
    try:
        with MemorySampler() as memory:
            settings = Settings.from_environment()
            started = time.perf_counter()
            encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
            if encoder is None:
                raise ValueError("actual_encoder_required")
            report["startup"] = {"domain_import_ms": None, "encoder_load_ms": (time.perf_counter() - started) * 1000}
            encoder = TimedEncoder(encoder)
            engine = create_runtime_engine(settings.database_url)
            repository = CatalogRepository(engine)
            page = repository.search("", 256, 0)
            if page.total != len(page.items) or page.total > 256 or page.catalog_version != encoder.catalog_version:
                raise ValueError("catalog_inventory_or_encoder_mismatch")
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            if page.catalog_version != manifest["catalog_version"]:
                raise ValueError("frozen_catalog_version_mismatch")
            report.update(catalog_version=page.catalog_version, eligible_games=page.total,
                model=settings.groq_model if args.mode != "offline" else "scripted-no-provider",
                catalog_evidence={str(g.app_id): {"title": g.title, "description": g.description,
                    "modes": g.modes, "platforms": g.platforms, "genres": g.genres, "tags": g.tags,
                    "price": g.price.model_dump(mode="json") if g.price else None} for g in page.items})
            games = {g.app_id: g for g in page.items}
            if args.mode != "offline":
                if not settings.ai_enabled or not settings.groq_api_key.get_secret_value():
                    raise ValueError("configured_ai_and_key_required")
                # Assert this is the same project checked by the owner's budget preflight.
                if "mmdmxjiawlbridvvhtrt" not in str(engine.url.host) + str(engine.url.username):
                    raise ValueError("budget_preflight_project_mismatch")
                report["approval"] = policy["live_pilot"]
                budget = CappedBudget(DatabaseBudget(engine, settings.ai_daily_calls, settings.ai_daily_tokens), report, path)
                model = JournalModel(GroqAssistant(settings, budget), report, path)
                selected = [c for c in cases if c["id"] == "M01"]
            else:
                selected = [c for c in cases if c["source"] == "real_catalog" and (args.split == "all" or c["split"] == args.split)]
            save(path, report)
            throttle = ClientThrottle()
            for case in selected:
                for method in (("proposed",) if args.mode == "retest" else METHODS):
                    state, messages = ChatStateV2(), []
                    for index in range(len(case["turns"])):
                        previous = next((r for r in report["records"] if r["case_id"] == case["id"]
                            and r["method"] == method and r["turn"] == index + 1), None)
                        if previous:
                            if previous["status"] != "ok":
                                break
                            response = previous["response"]
                            state = ChatStateV2.model_validate(response["state"])
                            messages += [ConversationMessage(role="user", content=previous["user"]),
                                         ConversationMessage(role="assistant", content=response["message"])]
                            continue
                        if args.mode == "offline":
                            model = OracleModel(oracle_plan(case, index, games, policy))
                        else:
                            if any(a.get("reservation") in {"granted", "pending"} and a["status"] == "started"
                                   for a in report["provider_attempts"]):
                                raise ValueError("indeterminate_provider_attempt_requires_owner_review")
                            last = max(report.get("last_turn_started_epoch", 0), report.get("last_turn_completed_epoch", 0))
                            time.sleep(max(0, 30.1 - (time.time() - last)))
                            if not throttle.allow("r4-evaluation"):
                                raise ValueError("peer_throttle_denied")
                        rag_type = RecordedRAG if method == "proposed" else SemanticBaseline
                        rag = rag_type(model, repository, encoder)
                        state, messages = record_turn(case, index, method, rag, model, state, messages, encoder, report, path)
                        if state is None:
                            break
                        # Each RunnableSequence holds bound methods. Release its
                        # cycle between samples, outside measured turn latency.
                        del rag
                        gc.collect()
            report["summary"] = summarize(report)
            report["split_summaries"] = {split: summarize({"records": [r for r in report["records"] if r["split"] == split]})
                                         for split in ("development", "held_out")}
            report["peak_sampled_rss_mib"] = memory.peak / 1024**2
            report["finished_at"] = datetime.now(UTC).isoformat()
            report["status"] = "completed_with_failures" if any(r["status"] != "ok" for r in report["records"]) else "completed"
            save(path, report)
            print(json.dumps({"status": report["status"], "mode": args.mode, "summary": report["summary"],
                "provider_attempts": len(report["provider_attempts"]), "quota_reservations": report["actual_quota_reservations"],
                "peak_sampled_rss_mib": report["peak_sampled_rss_mib"]}))
    finally:
        if engine is not None:
            engine.dispose()
        lock.close()
        lock_path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["offline", "pilot", "retest"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--split", choices=["development", "held_out", "all"], default="all")
    args = parser.parse_args()
    if args.mode == "offline" and args.output is None:
        parser.error("offline requires --output")
    if args.mode != "offline" and args.output is not None:
        parser.error("pilot uses its single fixed durable approval ledger, not a new output path")
    try:
        run(args)
    except Exception as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__, "detail": "evaluation_stopped_no_automatic_retry"}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
