"""Measure a real one-worker HTTP process with encoder, validation and DB probe."""

import json
import os
import socket
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def process_tree_memory(root):
    """Windows venv launchers may spawn the actual interpreter as a child."""
    import psutil

    processes = [root] + root.children(recursive=True)
    resident = 0
    live = []
    for process in processes:
        try:
            resident += process.memory_info().rss
            live.append(process)
        except psutil.Error:
            pass
    return resident, live


def run_api_benchmark(cache_dir: Path, env_file: Path, output: Path) -> int:
    import numpy as np
    import psutil
    from huggingface_hub import hf_hub_download

    from game_discovery.jobs.encoder_benchmark import MODEL, REVISION, TEXTS
    from game_discovery.jobs.encoder_parity import PARITY_TEXTS

    # Preparation only; the API receives immutable local paths, never downloads.
    paths = {name: hf_hub_download(MODEL, name, revision=REVISION, cache_dir=str(cache_dir), local_files_only=True)
             for name in ("tokenizer.json", "onnx/model.onnx")}
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    environment = {**os.environ, "M0_TOKENIZER_PATH": paths["tokenizer.json"],
                   "M0_MODEL_PATH": paths["onnx/model.onnx"], "M0_ENV_FILE": str(env_file.resolve())}
    started = time.perf_counter()
    child = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "game_discovery.jobs.api_spike:app", "--host", "127.0.0.1",
         "--port", str(port), "--workers", "1", "--no-access-log", "--log-level", "error"],
        env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    process = psutil.Process(child.pid)
    stop = threading.Event()
    peak = 0
    peak_process_count = 0
    observed_processes = {}

    def sample_memory():
        nonlocal peak, peak_process_count
        while not stop.is_set():
            try:
                resident, processes = process_tree_memory(process)
                peak = max(peak, resident)
                peak_process_count = max(peak_process_count, len(processes))
                observed_processes.update({item.pid: item for item in processes})
            except psutil.Error:
                return
            stop.wait(0.01)

    sampler = threading.Thread(target=sample_memory, daemon=True)
    sampler.start()
    base = f"http://127.0.0.1:{port}"

    def request(route, text=None):
        body = json.dumps({"text": text}).encode() if text is not None else None
        req = Request(base + route, data=body, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=20) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    try:
        deadline = started + 30
        while time.perf_counter() < deadline:
            if child.poll() is not None:
                raise ValueError("API resource process exited before startup")
            try:
                status, _ = request("/health/live")
                if status == 200:
                    break
            except (URLError, OSError):
                time.sleep(0.05)
        else:
            raise ValueError("API resource process startup timed out")
        startup_ms = (time.perf_counter() - started) * 1000
        readiness_status, readiness = request("/health/ready")
        if readiness_status != 503 or not readiness["encoder_available"] or not readiness["database_available"]:
            raise ValueError("API resource process is missing required spike dependencies")
        measurements = {}
        for label, texts in (("warm_short", [TEXTS[i % 8] for i in range(24)]),
                             ("warm_long", [PARITY_TEXTS[13]] * 12)):
            durations = []
            for text in texts:
                query_started = time.perf_counter()
                status, body = request("/spike/encode", text)
                durations.append((time.perf_counter() - query_started) * 1000)
                vector = np.array(body.get("embedding", []))
                if status != 200 or vector.shape != (384,) or not np.isfinite(vector).all() or not np.isclose(np.linalg.norm(vector), 1, atol=1e-5):
                    raise ValueError("API spike returned an invalid embedding")
            measurements[label] = {"samples": len(texts), "p50_ms": round(float(np.percentile(durations, 50)), 2),
                                   "p95_ms": round(float(np.percentile(durations, 95)), 2)}
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(lambda _: request("/spike/encode", PARITY_TEXTS[13])[0], range(8)))
        report = {
            "schema_version": 1, "measured_at": datetime.now(UTC).isoformat(), "model": MODEL,
            "revision": REVISION, "workers": 1, "concurrent_inference_limit": 1,
            "startup_ms": round(startup_ms, 2), "peak_sampled_api_rss_bytes": peak,
            "peak_sampled_api_rss_mib": round(peak / 1024**2, 2),
            "sampled_process_tree_max_processes": peak_process_count,
            "memory_basis": "sum of launcher plus descendant RSS; shared pages may be counted twice",
            "below_400_mb_memory_target": peak < 400_000_000,
            "http_latency": measurements, "two_client_status_counts": dict(Counter(statuses)),
            "readiness": readiness,
            "limitations": ["Local HTTP spike on 127.0.0.1, not deployed application or Render CPU evidence.",
                            "No active catalog/ranking/LLM; readiness correctly remains 503.",
                            "Memory covers validation, serialized vectors, bounded inference and real read-only database probe."]}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"job": "api-benchmark", "status": "ok" if report["below_400_mb_memory_target"] else "failed", "report": str(output)}))
        return 0 if report["below_400_mb_memory_target"] else 1
    finally:
        stop.set()
        sampler.join()
        # Stop only this benchmark's observed descendants, not unrelated Python jobs.
        for item in reversed(list(observed_processes.values())):
            try:
                item.terminate()
            except psutil.Error:
                pass
        _, alive = psutil.wait_procs(list(observed_processes.values()), timeout=5)
        for item in alive:
            try:
                item.kill()
            except psutil.Error:
                pass
        if child.poll() is None:
            child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
