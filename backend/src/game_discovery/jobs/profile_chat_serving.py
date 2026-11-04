"""Observe unchanged R4 evaluation: separate exact journal wrapper time from serving.

No replacement model/transport, extra inference, packet changes, retries or raw
tracing. The sidecar retains timings and curated case/turn/method identifiers only.
Serving-equivalent DOMAIN latency excludes evaluation wrappers, not real budget
SQL. It is not browser/HTTP latency; profiling overhead remains conservatively in it.
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.ai.provider import DatabaseBudget, GroqAssistant
from game_discovery.ai.rag import ConversationalRAG
from game_discovery.jobs.chat_evaluation import METHODS, percentile, sha256
from game_discovery.jobs.continue_chat_evaluation import PATHS, identity, run
from game_discovery.jobs.evaluate_chat import CappedBudget, JournalModel, record_turn, save


class ServingProfiler:
    def __init__(self, codes=None, clock=time.perf_counter):
        self.codes = codes or {
            record_turn.__code__: "turn", ConversationalRAG.invoke.__code__: "invoke",
            JournalModel.complete.__code__: "journal", GroqAssistant.complete.__code__: "transport",
            CappedBudget.reserve.__code__: "capped_budget", DatabaseBudget.reserve.__code__: "database_budget"}
        self.clock, self.stack, self.active, self.records, self.seen = clock, {}, None, [], set()

    def __call__(self, frame, event, arg):
        if event not in {"call", "return"}:
            return
        name = self.codes.get(frame.f_code)
        if name is None:
            return
        if event == "call":
            if name == "turn":
                values = frame.f_locals
                self.active = {"case_id": values["case"]["id"], "turn": values["index"] + 1,
                               "method": values["method"], "elapsed": {}, "calls": {}}
            if self.active is not None:
                self.stack[id(frame)] = (name, self.clock())
            return
        previous = self.stack.pop(id(frame), None)
        if previous is None or self.active is None:
            return
        name, start = previous
        elapsed = (self.clock() - start) * 1000
        self.active["elapsed"][name] = self.active["elapsed"].get(name, 0) + elapsed
        self.active["calls"][name] = self.active["calls"].get(name, 0) + 1
        if name == "invoke":
            values = self.active["elapsed"]
            # Journal exclusive time excludes its nested real transport; capped
            # budget exclusive time excludes nested real accounting SQL. Their
            # two differences do not overlap; nested saves are counted once.
            wrappers = (values.get("journal", 0) - values.get("transport", 0)
                        + values.get("capped_budget", 0) - values.get("database_budget", 0))
            self.active.update(invocation_ms=elapsed, evaluation_wrapper_ms=wrappers,
                               serving_equivalent_domain_ms=elapsed - wrappers,
                               invocation_returned_result=arg is not None,
                               warm=self.active["method"] in self.seen)
            self.seen.add(self.active["method"])
        if name == "turn":
            self.records.append(self.active)
            self.active = None


def summarize(records):
    result = {}
    for method in METHODS:
        rows = [r for r in records if r["method"] == method and r.get("warm")]
        result[method] = {"warm_samples": len(rows),
            "failed_samples": sum(not r["invocation_returned_result"] for r in rows),
            "journaled_domain_p95_ms": percentile([r["invocation_ms"] for r in rows]),
            "evaluation_wrapper_p95_ms": percentile([r["evaluation_wrapper_ms"] for r in rows]),
            "serving_equivalent_domain_p95_ms": percentile([r["serving_equivalent_domain_ms"] for r in rows])}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split", choices=PATHS)
    parser.add_argument("--quota-day", required=True)
    parser.add_argument("--used-calls", type=int, required=True)
    parser.add_argument("--used-tokens", type=int, required=True)
    parser.add_argument("--max-new-turns", type=int, choices=range(1, 89), default=6)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("new_sidecar_in_existing_directory_required")
    if not 0 <= args.used_calls <= 50 or not 0 <= args.used_tokens <= 500000:
        parser.error("quota receipt outside application limits")
    if sys.getprofile() is not None:
        raise ValueError("existing_profiler_would_be_overwritten")
    checkpoint = PATHS[args.split]
    sidecar = {"schema_version": 1, "status": "started", "started_at": datetime.now(UTC).isoformat(),
        "protocol": __doc__, "profiler_sha256": sha256(Path(__file__)), "source_identity": identity(args.split),
        "checkpoint_sha256_before": sha256(checkpoint) if checkpoint.exists() else None,
        "records": [], "scope": "timing only; original runner/model/accounting/packets unchanged"}
    save(args.output, sidecar)
    observer = ServingProfiler()
    try:
        sys.setprofile(observer)
        run(args)
        sidecar["status"] = "completed_observation"
    except Exception as error:
        sidecar.update(status="observation_stopped", error_type=type(error).__name__)
        raise
    finally:
        sys.setprofile(None)
        sidecar.update(records=observer.records, summary=summarize(observer.records),
                       checkpoint_sha256_after=sha256(checkpoint) if checkpoint.exists() else None,
                       finished_at=datetime.now(UTC).isoformat())
        save(args.output, sidecar)
        print(json.dumps({"timing_observation": sidecar["status"], "summary": sidecar["summary"]}))


if __name__ == "__main__":
    main()
