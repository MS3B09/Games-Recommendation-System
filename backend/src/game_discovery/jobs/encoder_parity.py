"""Separate CPU offline reference from online ONNX measurements."""

import importlib.metadata
import json
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.jobs.encoder_benchmark import MODEL, REVISION, TEXTS

PARITY_TEXTS = TEXTS + [
    "", "  \n ", "Café exploration — a hand-drawn world!", "co-op; crafting; story-rich",
    "combat progression exploration " * 100,
    "story atmosphere single-player " * 450,
    "A narrative adventure.\nWindows support and price are separate catalog constraints.",
    "I want games like Hades, but not a roguelike.",
]


class MemorySampler:
    def __init__(self):
        import psutil

        self.process = psutil.Process()
        self.peak = self.process.memory_info().rss
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self):
        while not self.stop.is_set():
            self.peak = max(self.peak, self.process.memory_info().rss)
            self.stop.wait(0.01)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join()


def run_reference(cache_dir: Path, output: Path) -> int:
    with MemorySampler() as memory:
        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        started = time.perf_counter()
        model = SentenceTransformer(MODEL, revision=REVISION, device="cpu", cache_folder=str(cache_dir))
        model.max_seq_length = 256
        loaded_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        vectors = model.encode(PARITY_TEXTS, batch_size=8, normalize_embeddings=True, show_progress_bar=False)
        report = {
            "model": MODEL, "revision": REVISION, "device": "cpu", "batch_size": 8,
            "max_tokens": 256, "vectors": vectors.tolist(),
            "load_including_first_download_ms": round(loaded_ms, 2),
            "encode_16_texts_ms": round((time.perf_counter() - started) * 1000, 2),
            "peak_sampled_rss_mb": round(memory.peak / 1024**2, 2),
            "versions": {name: importlib.metadata.version(name) for name in ("torch", "sentence-transformers", "transformers")},
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report) + "\n", encoding="utf-8")
    return 0


def run_parity(cache_dir: Path, output: Path) -> int:
    reference_path = output.with_name("offline-reference.json")
    completed = subprocess.run(
        [sys.executable, "-m", "game_discovery.jobs", "offline-reference",
         "--cache-dir", str(cache_dir), "--output", str(reference_path)],
        capture_output=True, text=True, timeout=420,
    )
    if completed.returncode:
        # Do not dump third-party logs; return a clean failure rather than fabricated parity.
        print(json.dumps({"job": "encoder-parity", "status": "failed", "phase": "offline_reference", "exit_code": completed.returncode}))
        return 1
    with MemorySampler() as memory:
        import numpy as np
        from huggingface_hub import hf_hub_download

        from game_discovery.retrieval.encoder import OnnxEncoder

        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        expected = np.array(reference.pop("vectors"), dtype=np.float32)
        tokenizer = Path(hf_hub_download(MODEL, "tokenizer.json", revision=REVISION, cache_dir=str(cache_dir)))
        runs = []
        for filename in ("onnx/model.onnx", "onnx/model_quint8_avx2.onnx"):
            path = Path(hf_hub_download(MODEL, filename, revision=REVISION, cache_dir=str(cache_dir)))
            encoder = OnnxEncoder(tokenizer, path)
            actual = encoder.encode(PARITY_TEXTS)
            cosines = np.sum(actual * expected, axis=1)
            max_error = float(np.max(np.abs(actual - expected)))
            timings = []
            for _ in range(12):
                started = time.perf_counter()
                encoder.encode([PARITY_TEXTS[13]])
                timings.append((time.perf_counter() - started) * 1000)
            runs.append({"file": filename, "cosine_min": float(cosines.min()),
                         "cosine_mean": float(cosines.mean()), "max_absolute_component_error": max_error,
                         "long_query_samples": 12, "long_query_p50_ms": float(np.percentile(timings, 50)),
                         "long_query_p95_ms": float(np.percentile(timings, 95))})
            del encoder
        passed = runs[0]["cosine_min"] >= 0.9999 and runs[0]["max_absolute_component_error"] <= 0.0001
        report = {"schema_version": 1, "measured_at": datetime.now(UTC).isoformat(),
                  "offline_reference": reference, "onnx_runs": runs,
                  "online_process_peak_sampled_rss_mb": round(memory.peak / 1024**2, 2),
                  "float_parity_thresholds": {"cosine_min": 0.9999, "max_absolute_component_error": 0.0001},
                  "float_parity_passed": passed,
                  "limitations": ["16 fixed texts including empty/Unicode/long inputs, not recommendation quality.",
                                  "CPU only; local hardware and no API server/concurrent traffic.",
                                  "Quantization not selected merely because representations are similar."]}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"job": "encoder-parity", "status": "ok" if passed else "failed", "report": str(output)}))
        return 0 if passed else 1
