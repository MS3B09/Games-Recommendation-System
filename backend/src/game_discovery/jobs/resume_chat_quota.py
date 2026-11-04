"""Quota-only operational amendment around unchanged v6 evaluation code.

Preserves frozen source hashes and prior output prefixes. No extra model calls,
transport retries, packet changes or paid resources. Provider rate observations
are a separate local sidecar; existing transport/accounting stay authoritative.
"""

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from game_discovery.ai import provider
from game_discovery.core.settings import Settings
from game_discovery.jobs import continue_chat_evaluation as runner
from game_discovery.jobs.chat_evaluation import ROOT, sha256
from game_discovery.jobs.evaluate_chat import save

AMENDMENT = ROOT / "data/evaluation/chat-rag-r4-quota-amendment.json"
RATE_PATH = Path("C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5/provider-free-rate-observations.json")
RATE_HEADERS = ("x-ratelimit-limit-requests", "x-ratelimit-limit-tokens", "x-ratelimit-remaining-requests",
                "x-ratelimit-remaining-tokens", "x-ratelimit-reset-requests", "x-ratelimit-reset-tokens", "retry-after")


class OperationalPause(Exception):
    pass


def prefix_digest(records, attempts):
    return hashlib.sha256(json.dumps([records, attempts], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def token_units(attempts, day):
    total = 0
    for attempt in attempts:
        if attempt.get("reservation") not in {"granted", "pending"} or not attempt["started_at"].startswith(day):
            continue
        usage = attempt.get("provider_usage", {}).get("total_tokens")
        total += usage if type(usage) is int else attempt["reserved_token_bound"]
    return total


def provider_day_units(day, current):
    paths = [ROOT / "docs/reports/conversational-rag-r4-pilot-revision.json"]
    folder = runner.JOURNALS["development"].parent
    for revision in range(2, 7):
        name = f"conversational-rag-r4-development-v{revision}.json"
        local, exported = folder / name, ROOT / "docs/reports" / name
        paths.append(local if revision >= 5 and local.exists() else exported)
    paths.append(runner.JOURNALS["held_out"])
    total = 0
    for path in paths:
        report = current if path == runner.JOURNALS[current["scope_split"]] else (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {})
        total += token_units(report.get("provider_attempts", []), day)
    return total


def register_amendment(report, amendment, checkpoint_sha, wrapper_sha):
    existing = next((entry for entry in report.get("operational_amendments", []) if entry["id"] == amendment["id"]), None)
    if existing:
        if existing["amendment_sha256"] != sha256(AMENDMENT) or existing["wrapper_sha256"] != wrapper_sha:
            raise ValueError("operational_amendment_identity_changed")
        return
    if report["mode"] == "live_development" and checkpoint_sha != amendment["development_checkpoint_sha256_before_amendment"]:
        raise ValueError("unexpected_pre_amendment_checkpoint")
    report.setdefault("operational_amendments", []).append({"id": amendment["id"],
        "registered_at": datetime.now(UTC).isoformat(), "amendment_sha256": sha256(AMENDMENT),
        "wrapper_sha256": wrapper_sha, "checkpoint_sha256_before": checkpoint_sha,
        "daily_limits": amendment["temporary_daily_limits"], "original_source_hashes_preserved": True})


def run(args):
    if args.quota_day != datetime.now(UTC).date().isoformat():
        raise ValueError("fresh_utc_day_quota_receipt_required")
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    settings = Settings.from_environment()
    if (settings.ai_daily_calls, settings.ai_daily_tokens, settings.groq_model) != (100, 1500000, "openai/gpt-oss-120b"):
        raise ValueError("approved_runtime_limits_and_original_model_required")
    path = runner.JOURNALS[args.split]
    if path.with_suffix(".json.lock").exists():
        raise ValueError("evaluation_lock_present")
    current = runner.identity(args.split)
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else current
    if report.get("status", "").startswith("completed"):
        return runner.run(args)
    if not runner.same_source(report, current):
        raise ValueError("frozen_source_changed_no_calls")
    if args.split == "held_out":
        development = json.loads(runner.JOURNALS["development"].read_text(encoding="utf-8"))
        if not runner.development_passed(development) or not runner.same_source(development, current):
            raise ValueError("same_version_development_gate_required")
    records_before, attempts_before = len(report["records"]), len(report["provider_attempts"])
    digest = prefix_digest(report["records"], report["provider_attempts"])
    if args.split == "development" and not report.get("operational_amendments"):
        backup = path.with_name(path.stem + "-before-quota-amendment.json")
        if backup.exists():
            if sha256(backup) != amendment["development_checkpoint_sha256_before_amendment"]:
                raise ValueError("pre_amendment_backup_identity_mismatch")
        else:
            save(backup, report)
            if sha256(backup) != amendment["development_checkpoint_sha256_before_amendment"]:
                raise ValueError("pre_amendment_backup_not_byte_exact")
    register_amendment(report, amendment, sha256(path) if path.exists() else None, sha256(Path(__file__)))
    report["scope_split"] = args.split
    save(path, report)
    save(runner.PATHS[args.split], report)
    limits = amendment["provider_free_safeguards"]
    rate = json.loads(RATE_PATH.read_text(encoding="utf-8")) if RATE_PATH.exists() else {"observations": []}
    original_urlopen, original_record = provider.urlopen, runner.record_turn

    def observe_open(*positional, **keywords):
        try:
            response = original_urlopen(*positional, **keywords)
        except HTTPError as error:
            headers = {key: error.headers.get(key) for key in RATE_HEADERS if error.headers.get(key) is not None}
            rate["observations"].append({"observed_at": datetime.now(UTC).isoformat(), "status": error.code, "headers": headers})
            raise
        headers = {key: response.headers.get(key) for key in RATE_HEADERS if response.headers.get(key) is not None}
        rate["observations"].append({"observed_at": datetime.now(UTC).isoformat(), "headers": headers})
        return response

    def guarded_turn(case, index, method, rag, model, state, messages, encoder, journal, journal_path):
        if datetime.now(UTC).date().isoformat() != args.quota_day:
            raise OperationalPause("paused_provider_day_changed")
        if any(a.get("http_status") in {429, 402} and a["started_at"].startswith(args.quota_day)
               for a in journal["provider_attempts"][-2:]):
            raise OperationalPause("paused_provider_rate_limit_review")
        spent = provider_day_units(args.quota_day, journal)
        if spent + limits["worst_case_turn_token_units"] > limits["conservative_local_tokens_per_day"]:
            raise OperationalPause("paused_provider_daily_token_headroom")
        if rate["observations"]:
            latest = rate["observations"][-1]
            if latest["observed_at"].startswith(args.quota_day):
                remaining = latest["headers"].get("x-ratelimit-remaining-requests")
                if remaining is not None and int(remaining) < 2:
                    raise OperationalPause("paused_provider_daily_request_headroom")
        last = max(journal.get("last_turn_started_epoch", 0), journal.get("last_turn_completed_epoch", 0))
        time.sleep(max(0, limits["evaluation_turn_spacing_seconds"] - (time.time() - last)))
        if datetime.now(UTC).date().isoformat() != args.quota_day:
            raise OperationalPause("paused_provider_day_changed")
        try:
            return original_record(case, index, method, rag, model, state, messages, encoder, journal, journal_path)
        finally:
            save(RATE_PATH, rate)

    try:
        with patch.object(provider, "urlopen", observe_open), patch.object(runner, "record_turn", guarded_turn):
            runner.run(args)
    except OperationalPause as error:
        report = json.loads(path.read_text(encoding="utf-8"))
        report["status"] = str(error)
        save(path, report)
        save(runner.PATHS[args.split], report)
        print(json.dumps({"status": str(error), "provider_calls_retried": 0}))
    finally:
        after = json.loads(path.read_text(encoding="utf-8"))
        if prefix_digest(after["records"][:records_before], after["provider_attempts"][:attempts_before]) != digest:
            raise ValueError("pre_amendment_output_prefix_changed")
        save(RATE_PATH, rate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split", choices=runner.PATHS)
    parser.add_argument("--quota-day", required=True)
    parser.add_argument("--used-calls", type=int, required=True)
    parser.add_argument("--used-tokens", type=int, required=True)
    parser.add_argument("--max-new-turns", type=int, choices=range(1, 89), default=6)
    args = parser.parse_args()
    if not 0 <= args.used_calls <= 100 or not 0 <= args.used_tokens <= 1500000:
        parser.error("quota receipt exceeds approved operational limits")
    run(args)


if __name__ == "__main__":
    main()
