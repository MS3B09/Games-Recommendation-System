"""Isolated R0 orchestration experiment, never imported by the application.

All provider/retrieval stages are synthetic. Optional real local encoding is
measured separately and held resident in both API processes. No database/network
access, no quota reservations, no application settings edits, no model downloads.
"""

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


class Stages:
    """Same finite functions for both modes; no agent, retry or parallel path."""

    def __init__(self, core):
        self.core = core
        self.calls = 0
        self.visited = []

    def interpret(self, data):
        self.calls += 1
        self.visited.append("interpret")
        if data["kind"] == "provider_failure":
            raise RuntimeError("scripted_provider_failure")
        return {**data, "plan": {"kind": data["kind"], "query": "exploration"}}

    def retrieve(self, data):
        self.visited.append("retrieve")
        games = [] if data["kind"] in {"social", "clarify", "empty"} else [
            {"app_id": i + 1, "title": f"Synthetic evidence {i + 1}",
             "description": ("Catalog description about exploration and cooperative play. " * 12)[:640],
             "modes": ["single-player", "online-co-op"], "platforms": {"windows": True},
             "price": {"amount_cents": 1999, "observed_at": "2026-10-14T00:00:00Z"}}
            for i in range(8)]
        return {**data, "games": games}

    def evidence(self, data):
        self.visited.append("evidence")
        if self.core:
            from langchain_core.documents import Document

            # Exercise the proposed retriever/Document boundary with primitive,
            # canonical metadata, not a placeholder import of the library.
            documents = [Document(page_content=g["description"],
                metadata={key: value for key, value in g.items() if key != "description"}) for g in data["games"]]
            games = [{**d.metadata, "description": d.page_content} for d in documents]
        else:
            games = data["games"]
        packet = {"request": data["message"], "games": games}
        if len(json.dumps(packet, ensure_ascii=False).encode()) > 12000:
            raise ValueError("mock_evidence_over_budget")
        return {**data, "packet": packet}

    def generate(self, data):
        self.visited.append("generate")
        ids = [g["app_id"] for g in data["packet"]["games"]][:4]
        if ids:
            self.calls += 1
        return {**data, "answer": {"message": "Catalog evidence only.", "game_ids": ids}}

    def validate(self, data):
        self.visited.append("validate")
        if set(data["answer"]["game_ids"]) - {g["app_id"] for g in data["games"]}:
            raise ValueError("invented_selection")
        return data["answer"]

    def functions(self):
        return [self.interpret, self.retrieve, self.evidence, self.generate, self.validate]


def worker(args):
    # Explicitly prevent accidentally inherited LangSmith/legacy tracing or
    # configured Groq/DB access, including module-level create_app().
    for key in list(os.environ):
        if key.startswith(("LANGCHAIN_", "LANGSMITH_")) or key in {
            "DATABASE_URL", "GROQ_API_KEY", "QUERY_MODEL_PATH", "QUERY_TOKENIZER_PATH", "QUERY_ARTIFACT_PATH"}:
            os.environ.pop(key, None)
    os.environ.update({"LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false",
        "GAME_DISCOVERY_ENV_FILE": os.devnull, "AI_ENABLED": "false"})
    import psutil

    process = psutil.Process()
    from game_discovery.jobs.encoder_parity import MemorySampler

    with MemorySampler() as memory:
        started = time.perf_counter()
        from fastapi.testclient import TestClient
        from game_discovery.api.main import create_app
        from game_discovery.catalog.contracts import Filters
        from game_discovery.catalog.discovery import recommendation
        from game_discovery.catalog.repository import CatalogRepository
        from game_discovery.core.settings import Settings

        api_import_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        stages = Stages(args.worker == "core")
        local_events = []
        if args.worker == "core":
            from langchain_core.callbacks import BaseCallbackHandler
            from langchain_core.runnables import RunnableLambda, RunnableSequence

            class StageNames(BaseCallbackHandler):
                # Deliberately retain names only, never prompts/documents/output.
                def on_chain_start(self, serialized, inputs, *, name=None, **kwargs):
                    local_events.append(name)

            chain = RunnableSequence(*[RunnableLambda(f, name=f.__name__) for f in stages.functions()])
            config = {"callbacks": [StageNames()], "max_concurrency": 1}
            def invoke(data):
                return chain.invoke(data, config=config)
            graph_nodes = [n.name for n in chain.get_graph().nodes.values()]
        else:
            def invoke(data):
                for function in stages.functions():
                    local_events.append(function.__name__)
                    data = function(data)
                return data

            graph_nodes = [f.__name__ for f in stages.functions()]
        orchestration_import_ms = (time.perf_counter() - started) * 1000

        # Socket guard makes a tracing/provider/network regression fail loudly.
        durations, results, calls = [], [], []
        with patch("socket.socket.connect", side_effect=AssertionError("R0 network access forbidden")), \
                patch("socket.socket.connect_ex", side_effect=AssertionError("R0 network access forbidden")):
            for _ in range(10):
                invoke({"kind": "recommend", "message": "Find cooperative exploration games."})
            for i in range(100):
                kind = ("recommend", "title_lookup", "social", "clarify", "empty")[i % 5]
                before = stages.calls
                started = time.perf_counter()
                answer = invoke({"kind": kind, "message": "Find cooperative exploration games."})
                durations.append((time.perf_counter() - started) * 1000)
                calls.append(stages.calls - before)
                results.append(answer)
            before = stages.calls
            try:
                invoke({"kind": "provider_failure", "message": "Fail once."})
            except RuntimeError as error:
                if str(error) != "scripted_provider_failure":
                    raise
            else:
                raise AssertionError("Provider failure was hidden")
            failure_calls = stages.calls - before
            if calls != [2, 2, 1, 1, 1] * 20 or failure_calls != 1:
                raise AssertionError("Call-count parity failed")
            # Named stage replacement: swap only evidence retrieval, retain the
            # other runnables. This is the concrete composition/testing experiment.
            if args.worker == "core":
                def no_evidence(data):
                    return {**data, "games": []}
                swapped = RunnableSequence(chain.steps[0], RunnableLambda(no_evidence), *chain.steps[2:])
                isolated = swapped.invoke({"kind": "recommend", "message": "No evidence"}, config={"callbacks": []})
                assert isolated["game_ids"] == []

        warm_orchestration_rss = process.memory_info().rss
        encoding = []
        from game_discovery.retrieval.query import load_query_encoder

        started = time.perf_counter()
        encoder = load_query_encoder(args.tokenizer, args.model, args.artifact)
        encoder_load_ms = (time.perf_counter() - started) * 1000
        if encoder is None:
            raise AssertionError("Representative API requires real pinned local encoder")
        for text in ["cooperative exploration", "single-player combat progression", "story exploration " * 200]:
            started = time.perf_counter()
            vector = encoder(text)
            assert len(vector) == 384
            encoding.append((time.perf_counter() - started) * 1000)

        # Existing real FastAPI route/serialization, synthetic repository and
        # provider. One turn preserves the real throttle (no interval bypass).
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
        from test_catalog_m2 import fixture

        repo = MagicMock(spec=CatalogRepository)
        game = fixture()
        repo.discover.return_value = (encoder.catalog_version, [recommendation(game, [], Filters())])
        model = MagicMock()
        model.complete.side_effect = [{"mode": "search", "query": "exploration"},
            {"message": "Explore this catalog option.", "game_ids": [game.app_id]}]
        app = create_app(Settings(ai_enabled=False), repository=repo, chat_model=model, query_encoder=encoder)
        with TestClient(app) as client:
            reply = client.post("/api/v1/chat", json={"message": "Find exploration games."})
            assert reply.status_code == 200 and len(reply.json()["games"]) == 1
        assert model.complete.call_count == 2
        warm_api_rss = process.memory_info().rss
        # Include platform lifetime high-water working set as well as 10ms samples.
        info = process.memory_info()
        peak = max(memory.peak, getattr(info, "peak_wset", info.rss))

    packages = {d.metadata["Name"].lower().replace("_", "-"): d.version
                for d in importlib.metadata.distributions()}
    return {"mode": args.worker, "warm_repetitions": 100,
        "api_import_ms": api_import_ms, "orchestration_import_build_ms": orchestration_import_ms,
        "warm_orchestration_rss_bytes": warm_orchestration_rss, "warm_api_rss_bytes": warm_api_rss,
        "representative_api_peak_rss_bytes": peak,
        "orchestration_p50_ms": statistics.median(durations), "orchestration_p95_ms": percentile(durations, .95),
        "result_digest": hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest(),
        "mock_call_counts": calls, "failure_calls_without_retry": failure_calls,
        "representative_api_mock_calls": model.complete.call_count,
        "local_stage_names_observed": sorted(set(local_events)), "graph_nodes": graph_nodes,
        "encoder_load_ms": encoder_load_ms, "encoder_sample_ms": encoding,
        "packages": packages, "live_provider_calls": 0, "network_during_composition": "forbidden"}


def run(args):
    trials = []
    for trial in range(3):
        pair = {}
        for mode in (("direct", "core") if trial % 2 == 0 else ("core", "direct")):
            python = getattr(args, mode + "_python")
            started = time.perf_counter()
            completed = subprocess.run([python, str(Path(__file__).resolve()), "--worker", mode,
                "--tokenizer", args.tokenizer, "--model", args.model, "--artifact", args.artifact],
                capture_output=True, text=True, timeout=120)
            if completed.returncode:
                # This isolated child never receives DB/key configuration, but do
                # not dump arbitrary third-party logs into persistent reports.
                raise RuntimeError(f"Isolated {mode} worker failed: {completed.stderr[-1800:]}")
            pair[mode] = json.loads(completed.stdout)
            pair[mode]["child_wall_ms"] = (time.perf_counter() - started) * 1000
        trials.append(pair)
    direct, core = trials[0]["direct"], trials[0]["core"]
    added_packages = {k: v for k, v in core["packages"].items() if k not in direct["packages"]}
    changed_packages = {k: [v, core["packages"].get(k)] for k, v in direct["packages"].items()
                        if core["packages"].get(k) != v}
    deltas = [{"orchestration_p95_ms": p["core"]["orchestration_p95_ms"] - p["direct"]["orchestration_p95_ms"],
               "warm_orchestration_rss_mib": (p["core"]["warm_orchestration_rss_bytes"] -
                   p["direct"]["warm_orchestration_rss_bytes"]) / 1024**2,
               "warm_api_rss_mib": (p["core"]["warm_api_rss_bytes"] - p["direct"]["warm_api_rss_bytes"]) / 1024**2}
              for p in trials]
    parity = all(p["core"]["result_digest"] == p["direct"]["result_digest"] and
                 p["core"]["mock_call_counts"] == p["direct"]["mock_call_counts"] for p in trials)
    gates = {"results_and_calls_identical": parity,
        "added_orchestration_p95_at_most_25_ms": all(d["orchestration_p95_ms"] <= 25 for d in deltas),
        "added_warm_rss_at_most_30_mib": all(max(d["warm_orchestration_rss_mib"], d["warm_api_rss_mib"]) <= 30
                                              for d in deltas),
        "core_representative_peak_below_400_mib": all(p["core"]["representative_api_peak_rss_bytes"] < 400 * 1024**2
                                                    for p in trials),
        "no_baseline_dependency_version_changes": not changed_packages}
    report = {"schema_version": 1, "measured_at": datetime.now(UTC).isoformat(),
        "platform": platform.platform(), "python": platform.python_version(),
        "trials": trials, "paired_deltas": deltas, "gates": gates, "all_numeric_gates_passed": all(gates.values()),
        "added_packages": added_packages, "changed_packages": changed_packages,
        "experiment_lock_bytes": Path(__file__).with_name("uv.lock").stat().st_size,
        "production_lock_bytes": Path(__file__).resolve().parents[2].joinpath("uv.lock").stat().st_size,
        "limitations": ["New retrieval/intent/state contracts are NOT implemented by this prototype.",
            "100 warm mocked repetitions per method per fresh child; three alternating pairs, sequential CPU operation.",
            "Provider and retrieval synthetic; separate real ONNX samples are not included in orchestration timings.",
            "Representative existing FastAPI chat uses TestClient, one card, real encoder, synthetic provider/repository.",
            "Core pipeline is resident alongside existing API, not installed in the application's dependency environment.",
            "Per-interpreter RSS/high-water working set, not venv launcher tree or hosted/container memory.",
            "Cold timings are fresh interpreter imports with filesystem caches, not a cold machine."]}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed" if all(gates.values()) else "decision_required",
                      "gates": gates, "paired_deltas": deltas, "added_packages": added_packages}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=("direct", "core"))
    parser.add_argument("--direct-python")
    parser.add_argument("--core-python")
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.worker:
        print(json.dumps(worker(arguments)))
    else:
        run(arguments)
