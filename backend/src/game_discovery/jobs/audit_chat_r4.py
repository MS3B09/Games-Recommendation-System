"""Read-only R4 evidence reconciliation; no provider, database or reservations."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.jobs.chat_evaluation import ROOT, load_cases, sha256
from game_discovery.jobs.evaluate_chat import save
from game_discovery.jobs.continue_chat_evaluation import identity, same_source

REPORTS = ROOT / "docs/reports"
ORIGINALS = {
    "conversational-rag-r4-pilot.json": "2c81d8ce86a3cddd11029db6a3f696df55e92c56ceb15f1994b8e07f09312180",
    "conversational-rag-r4-pilot-revision.json": "7583963d04670accb421847c68db4ac4ead5406131447e58cfa62d803495ccea",
}


def audit():
    result = {"provider_calls": 0, "quota_reservations": 0, "original_ledger_hashes": {}, "continuation": {}}
    for name, expected in ORIGINALS.items():
        actual = sha256(REPORTS / name)
        result["original_ledger_hashes"][name] = {"sha256": actual, "unchanged": actual == expected}
    all_attempts = []
    for revision in (2, 3, 4, 5, 6):
        export = REPORTS / f"conversational-rag-r4-development-v{revision}.json"
        local = Path("C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5") / export.name
        path = local if revision >= 5 and local.exists() else export
        if not path.exists():
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        attempts = report["provider_attempts"]
        usage = [a["provider_usage"] for a in attempts if a.get("provider_usage")]
        all_attempts += attempts
        present = {(r["case_id"], r["turn"], r["method"]) for r in report["records"]}
        missing = [f'{c["id"]}:{t + 1}:{method}' for c in load_cases()
                   if c["source"] == "real_catalog" and c["split"] == "development"
                   for t in range(len(c["turns"])) for method in report["methods"]
                   if (c["id"], t + 1, method) not in present]
        result["continuation"][str(revision)] = {
            "status": report["status"], "records": len(report["records"]),
            "authoritative_path": str(path),
            "workspace_export_matches_authoritative": export.exists() and sha256(export) == sha256(path),
            "not_attempted_method_turns": missing,
            "source_identity_matches_current": same_source(report, identity("development")),
            "calls": sum(a.get("reservation") == "granted" for a in attempts),
            "reserved_tokens": sum(a["reserved_token_bound"] for a in attempts if a.get("reservation") == "granted"),
            "actual_provider_usage": {key: sum(u[key] for u in usage) for key in
                ("prompt_tokens", "completion_tokens", "total_tokens")} if len(usage) == len(attempts) else None,
            "calls_with_reported_usage": len(usage),
            "known_provider_tokens": sum(u.get("total_tokens", 0) for u in usage),
            "proposed_recommendation_without_retrieval": [f'{r["case_id"]}:{r["turn"]}' for r in report["records"]
                if r["method"] == "proposed" and r.get("plan", {}).get("kind") == "recommend"
                and r.get("response", {}).get("retrieval") is None],
            "peak_sampled_rss_mib": report.get("peak_sampled_rss_mib"),
            "summary": report.get("summary", "interrupted_before_summary"), "sha256": sha256(path)}
    held_export = REPORTS / "conversational-rag-r4-held_out-v6.json"
    held_local = Path("C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5") / held_export.name
    held_path = held_local if held_local.exists() else held_export
    held_calls, held_reserved = 0, 0
    if held_path.exists():
        held = json.loads(held_path.read_text(encoding="utf-8"))
        all_attempts += held["provider_attempts"]
        held_calls = sum(a.get("reservation") == "granted" for a in held["provider_attempts"])
        held_reserved = sum(a["reserved_token_bound"] for a in held["provider_attempts"] if a.get("reservation") == "granted")
        result["held_out_v6"] = {"status": held["status"], "records": len(held["records"]),
            "calls": held_calls, "reserved_tokens": held_reserved, "sha256": sha256(held_path),
            "source_identity_matches_current": same_source(held, identity("held_out")),
            "workspace_export_matches_authoritative": sha256(held_export) == sha256(held_path),
            "summary": held["summary"], "failure_cases": [{"case_id": r["case_id"], "turn": r["turn"],
                "method": r["method"], "error_code": r.get("error_code"), "error_type": r.get("error_type")}
                for r in held["records"] if r["status"] != "ok"]}
        from game_discovery.jobs.resume_chat_quota import provider_day_units
        today = datetime.now(UTC).date().isoformat()
        result["provider_local_conservative_token_units"] = {"utc_day": today, "units": provider_day_units(today, held),
            "next_worst_case_turn_units": 26560, "daily_guard": 200000,
            "scope": "Owned-journal usage, not a claim of exact organization/provider quota exhaustion"}
    backup = Path("C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5/conversational-rag-r4-development-v6-before-quota-amendment.json")
    if backup.exists():
        from game_discovery.jobs.resume_chat_quota import prefix_digest
        before = json.loads(backup.read_text(encoding="utf-8"))
        current = json.loads(Path(result["continuation"]["6"]["authoritative_path"]).read_text(encoding="utf-8"))
        result["quota_amendment_prefix_proof"] = {"backup_sha256": sha256(backup),
            "records": len(before["records"]), "attempts": len(before["provider_attempts"]),
            "unchanged": prefix_digest(before["records"], before["provider_attempts"]) == prefix_digest(
                current["records"][:len(before["records"])], current["provider_attempts"][:len(before["provider_attempts"])])}
    # The revision ledger already includes original pilot attempts. Count it once.
    initial = json.loads((REPORTS / "conversational-rag-r4-pilot-revision.json").read_text(encoding="utf-8"))
    all_attempts += initial["provider_attempts"]
    daily = {}
    for attempt in all_attempts:
        if attempt.get("reservation") != "granted":
            continue
        day = attempt["started_at"].split("T")[0]
        row = daily.setdefault(day, {"calls": 0, "reserved_tokens": 0})
        row["calls"] += 1
        row["reserved_tokens"] += attempt["reserved_token_bound"]
    result["daily_journal_start_utc_attribution"] = daily
    result["accounting_reconciliation"] = {
        "calls": initial["live_provider_calls"] + sum(r["calls"] for r in result["continuation"].values()) + held_calls,
        "reserved_tokens": sum(a["reserved_token_bound"] for a in initial["provider_attempts"]
            if a.get("reservation") == "granted") + sum(r["reserved_tokens"] for r in result["continuation"].values()) + held_reserved,
        "scope": "Original/revision aggregate once plus disjoint v2-v6 development and v6 held-out attempts across UTC days; compare daily attribution with read-only SQL receipts."}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and (args.output.exists() or not args.output.parent.is_dir()):
        parser.error("Use a new output in an existing parent")
    result = audit()
    if args.output:
        save(args.output, result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
