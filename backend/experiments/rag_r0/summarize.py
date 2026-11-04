"""Derive a compact R0 decision record from retained raw evidence; no reruns."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORTS = ROOT / "docs/reports"


def main():
    raw = json.loads((REPORTS / "conversational-rag-r0-benchmark.json").read_text(encoding="utf-8"))
    trials = raw["trials"]
    paired = raw["paired_deltas"]
    lock = HERE / "uv.lock"
    direct_lock = HERE / "direct-lock/uv.lock"
    summary = {
        "schema_version": 1,
        "decision": "Use langchain-core==1.7.0 for finite chat composition in R2; R1/R2 still require owner approval.",
        "numeric_gates": raw["gates"],
        "mocked_warm_repetitions_per_method": sum(t["core"]["warm_repetitions"] for t in trials),
        "worst_added_orchestration_p95_ms": max(p["orchestration_p95_ms"] for p in paired),
        "worst_added_warm_rss_mib": max(max(p["warm_orchestration_rss_mib"], p["warm_api_rss_mib"]) for p in paired),
        "core_peak_rss_mib": [t["core"]["representative_api_peak_rss_bytes"] / 1024**2 for t in trials],
        "core_import_and_build_ms": [t["core"]["orchestration_import_build_ms"] for t in trials],
        "direct_import_and_build_ms": [t["direct"]["orchestration_import_build_ms"] for t in trials],
        "dependency_delta": {"direct_installed": len(trials[0]["direct"]["packages"]),
            "core_installed": len(trials[0]["core"]["packages"]), "added": raw["added_packages"],
            "changed_baseline_versions": raw["changed_packages"]},
        "lockfile_delta": {"direct_control_bytes": direct_lock.stat().st_size,
            "core_experiment_bytes": lock.stat().st_size,
            "added_bytes": lock.stat().st_size - direct_lock.stat().st_size,
            "interpretation": "Isolated experiments, not a proposed production lockfile diff; control project names/path depths differ."},
        "benefits_demonstrated": ["Named five-stage Runnable graph can be inspected without executing a provider call.",
            "Local callback records stage names without retaining prompts/output or enabling hosted tracing.",
            "Retriever-to-Document adapter preserves identical evidence/output with the direct path.",
            "Retrieval stage can be replaced alone and produces a no-evidence outcome without rewriting other stages."],
        "tradeoffs": ["13 extra installed distributions, including mandatory langsmith dependency even with tracing disabled.",
            "Measured Core import/build cost 2.39–7.69 seconds on this local machine; no startup threshold was specified.",
            "Direct Python also supports stage injection; Core supplies a standard graph/callback vocabulary, not unique capability.",
            "All future adapters must keep metered ChatModel.complete and no retry/batch/parallel provider execution."],
        "model_parity_policy": {"representation": "all-MiniLM-L6-v2 pinned revision; 384 dimensions, normalized float ONNX",
            "existing_reference": "data/reports/offline-reference.json (ignored local artifact), historical data/reports/encoder-parity.json",
            "reference_sha256": hashlib.sha256((ROOT / "data/reports/offline-reference.json").read_bytes()).hexdigest(),
            "historical_parity_report_sha256": hashlib.sha256((ROOT / "data/reports/encoder-parity.json").read_bytes()).hexdigest(),
            "checks_now": "exact model/tokenizer SHA256, content-addressed manifest digest, unit-norm query, active-version existing vector query",
            "R1_exit": "repeat fixed 16-text ONNX/reference comparison with retained frozen reference if available; otherwise regenerate CPU reference separately offline",
            "thresholds": {"minimum_cosine": 0.9999, "maximum_absolute_component_error": 0.0001},
            "quantization": "not authorized as a silent representation replacement"},
        "live_provider_calls": 0, "database_writes": 0,
        "raw_benchmark_sha256": hashlib.sha256((REPORTS / "conversational-rag-r0-benchmark.json").read_bytes()).hexdigest(),
    }
    (REPORTS / "conversational-rag-r0-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
