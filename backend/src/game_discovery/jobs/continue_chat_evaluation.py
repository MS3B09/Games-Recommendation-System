"""Owner-approved R4 continuation; sequential, source-frozen, durable daily checkpoints.

Requires a fresh read-only shared quota receipt. Never replays attempts, resets
quotas or retries failed turns. Original pilot journals are never opened for write.
"""

import argparse
import gc
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.ai.chat_contracts import ChatStateV2
from game_discovery.ai.provider import ClientThrottle, DatabaseBudget, GroqAssistant
from game_discovery.catalog.contracts import ConversationMessage
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.jobs.chat_evaluation import MANIFEST, METHODS, ROOT, RecordedRAG, SemanticBaseline, load_cases, sha256
from game_discovery.jobs.encoder_parity import MemorySampler
from game_discovery.jobs.evaluate_chat import CappedBudget, JournalModel, TimedEncoder, header, record_turn, save, summarize
from game_discovery.retrieval.query import load_query_encoder

POLICY = ROOT / "data/evaluation/chat-rag-r4-continuation-v6.json"
PATHS = {split: ROOT / f"docs/reports/conversational-rag-r4-{split}-v6.json"
         for split in ("development", "held_out")}
JOURNALS = {split: Path("C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5") / path.name
            for split, path in PATHS.items()}
TURN_CALLS, TURN_TOKENS = 2, 26560


def identity(split):
    value = header("live_" + split)
    value.update(continuation_policy_sha256=sha256(POLICY), runner_sha256=sha256(Path(__file__)),
                 serving_source_sha256={str(p.relative_to(ROOT)): sha256(p) for folder in ("ai", "retrieval", "catalog", "db")
                     for p in sorted((ROOT / "backend/src/game_discovery" / folder).glob("*.py"))})
    return value


def same_source(report, current):
    keys = ("dataset_sha256", "manifest_sha256", "policy_sha256", "evaluator_sha256", "adapter_sha256",
            "serving_source_sha256", "continuation_policy_sha256", "runner_sha256")
    return all(report[k] == current[k] for k in keys)


def restore(previous, messages):
    response = previous["response"]
    messages += [ConversationMessage(role="user", content=previous["user"]),
                 ConversationMessage(role="assistant", content=response["message"])]
    messages = messages[-20:]
    while sum(len(m.content) for m in messages) > 12000:
        messages.pop(0)
    return ChatStateV2.model_validate(response["state"]), messages


def day_remaining(report, receipt, calls, tokens):
    """Subtract only attempts after this receipt; never double-count prior days."""
    new = report["provider_attempts"][receipt["attempt_offset"]:]
    return (calls - receipt["calls"] - sum(a.get("reservation") in {"pending", "granted"} for a in new),
            tokens - receipt["reserved_tokens"] - sum(a["reserved_token_bound"] for a in new
                if a.get("reservation") in {"pending", "granted"}))


def development_passed(report):
    expected = 13
    proposed = [r for r in report["records"] if r["method"] == "proposed"]
    return (report["status"].startswith("completed") and len(proposed) == expected
            and all(r["status"] == "ok" and not r["metrics"]["hard_card_violation_ids"]
                and not r["metrics"]["forbidden_card_ids_returned"]
                and all(v is not False for v in r["metrics"]["state_checks"].values())
                and r["metrics"]["target_hit_at_5"] is not False
                and r["metrics"]["expected_outcome_match"] is not False for r in proposed))


def run(args):
    if args.quota_day != datetime.now(UTC).date().isoformat():
        raise ValueError("fresh_utc_day_quota_preflight_required")
    path = JOURNALS[args.split]
    if not path.parent.is_dir():
        raise ValueError("approved_durable_journal_parent_required")
    current = identity(args.split)
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else current
    if report.get("status", "").startswith("completed"):
        print(json.dumps({"status": "already_completed_no_calls", "path": str(path)}))
        return
    if not same_source(report, current):
        raise ValueError("checkpoint_source_changed_no_calls")
    if any(a.get("reservation") in {"pending", "granted"} and a["status"] == "started"
           for a in report["provider_attempts"]):
        raise ValueError("indeterminate_attempt_requires_review_no_retry")
    if args.split == "held_out":
        development = json.loads(JOURNALS["development"].read_text(encoding="utf-8"))
        if not development_passed(development) or not same_source(development, current):
            raise ValueError("same_version_development_gate_required")
        report["development_ledger_sha256"] = sha256(JOURNALS["development"])
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    parent = policy.get("retained_parent")
    if parent:
        if sha256(ROOT / parent["path"]) != parent["sha256"]:
            raise ValueError("retained_parent_ledger_changed_no_calls")
        report["retained_parent"] = parent
    interrupted = policy.get("retained_interrupted_parent")
    if interrupted and sha256(ROOT / interrupted["path"]) != interrupted["sha256"]:
        raise ValueError("retained_interrupted_ledger_changed_no_calls")
    report["approval_limits"] = {k: policy[args.split][k] for k in ("max_calls", "max_reserved_tokens")}
    report["scope"] = f"Actual live {args.split} real-catalog paired comparison; human judgments pending"
    report["quality_gate"] = "incomplete: execution and owner human judgments required"
    report["durable_journal_path"] = str(path)
    report["workspace_export_path"] = str(PATHS[args.split])
    cases = [c for c in load_cases() if c["source"] == "real_catalog" and c["split"] == args.split]
    if args.split == "development":
        cases.sort(key=lambda c: policy["development"]["case_ids"].index(c["id"]))
    receipt = {"day": args.quota_day, "calls": args.used_calls, "reserved_tokens": args.used_tokens,
               "attempt_offset": len(report["provider_attempts"]), "recorded_at": datetime.now(UTC).isoformat()}
    report.setdefault("shared_quota_receipts", []).append(receipt)
    lock_path = path.with_suffix(".json.lock")
    lock = lock_path.open("x", encoding="utf-8")
    engine = None
    try:
        with MemorySampler() as memory:
            settings = Settings.from_environment()
            if not settings.ai_enabled or not settings.groq_api_key.get_secret_value():
                raise ValueError("configured_ai_and_key_required")
            started = time.perf_counter()
            encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
            if encoder is None:
                raise ValueError("actual_encoder_required")
            report.setdefault("startup", {"encoder_load_ms": (time.perf_counter() - started) * 1000})
            encoder = TimedEncoder(encoder)
            engine = create_runtime_engine(settings.database_url)
            if engine is None or "mmdmxjiawlbridvvhtrt" not in str(engine.url.host) + str(engine.url.username):
                raise ValueError("preflight_project_mismatch")
            repository = CatalogRepository(engine)
            page = repository.search("", 256, 0)
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            if page.total != 40 or page.catalog_version != encoder.catalog_version or page.catalog_version != manifest["catalog_version"]:
                raise ValueError("frozen_catalog_encoder_mismatch")
            report.update(catalog_version=page.catalog_version, model=settings.groq_model,
                          catalog_evidence={str(g.app_id): g.model_dump(mode="json") for g in page.items})
            model = JournalModel(GroqAssistant(settings, CappedBudget(DatabaseBudget(engine,
                settings.ai_daily_calls, settings.ai_daily_tokens), report, path)), report, path)
            throttle = ClientThrottle()
            report["status"] = "in_progress"
            save(path, report)
            new_turns = 0
            for case in cases:
                # Alternate order per case rather than always favor one method's warm cache.
                methods = METHODS if cases.index(case) % 2 == 0 else tuple(reversed(METHODS))
                for method in methods:
                    state, messages = ChatStateV2(), []
                    for index in range(len(case["turns"])):
                        previous = next((r for r in report["records"] if r["case_id"] == case["id"]
                            and r["method"] == method and r["turn"] == index + 1), None)
                        if previous:
                            if previous["status"] != "ok":
                                break
                            state, messages = restore(previous, messages)
                            continue
                        calls, tokens = day_remaining(report, receipt, settings.ai_daily_calls, settings.ai_daily_tokens)
                        if new_turns >= args.max_new_turns:
                            report["status"] = "paused_requested_checkpoint"
                            return
                        if datetime.now(UTC).date().isoformat() != receipt["day"] or calls < TURN_CALLS or tokens < TURN_TOKENS:
                            report.update(status="paused_daily_quota", remaining_observed_calls=calls,
                                          remaining_observed_reserved_tokens=tokens)
                            return
                        last = max(report.get("last_turn_started_epoch", 0), report.get("last_turn_completed_epoch", 0))
                        time.sleep(max(0, 30.1 - (time.time() - last)))
                        if datetime.now(UTC).date().isoformat() != receipt["day"]:
                            report["status"] = "paused_daily_quota"
                            return
                        if not throttle.allow("r4-evaluation"):
                            raise ValueError("peer_throttle_denied")
                        rag = (RecordedRAG if method == "proposed" else SemanticBaseline)(model, repository, encoder)
                        state, messages = record_turn(case, index, method, rag, model, state, messages, encoder, report, path)
                        save(PATHS[args.split], report)
                        new_turns += 1
                        del rag
                        gc.collect()
                        if state is None:
                            if method == "proposed" or any(a.get("http_status") == 400 for a in report["provider_attempts"][-2:]):
                                report["status"] = "paused_development_failure" if args.split == "development" else "paused_failed_turn_review"
                                return
                            break
            report["status"] = "completed_with_failures" if any(r["status"] != "ok" for r in report["records"]) else "completed"
            report["finished_at"] = datetime.now(UTC).isoformat()
    finally:
        if engine is not None:
            engine.dispose()
        report["summary"] = summarize(report)
        report["peak_sampled_rss_mib"] = max(report.get("peak_sampled_rss_mib", 0), memory.peak / 1024**2)
        save(path, report)
        save(PATHS[args.split], report)
        lock.close()
        lock_path.unlink()
        print(json.dumps({"status": report["status"], "attempts": len(report["provider_attempts"]),
                          "summary": report["summary"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split", choices=PATHS)
    parser.add_argument("--quota-day", required=True)
    parser.add_argument("--used-calls", type=int, required=True)
    parser.add_argument("--used-tokens", type=int, required=True)
    parser.add_argument("--max-new-turns", type=int, default=6, choices=range(1, 89))
    args = parser.parse_args()
    if not 0 <= args.used_calls <= 50 or not 0 <= args.used_tokens <= 500000:
        parser.error("quota receipt outside application limits")
    run(args)


if __name__ == "__main__":
    main()
