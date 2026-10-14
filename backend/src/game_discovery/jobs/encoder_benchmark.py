"""Disposable CPU feasibility spike, not the production query encoder."""

import gc
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
TEXTS = [
    "Satisfying single-player combat and progression with less repetition.",
    "A quiet farming game with friendships, crafting and exploration.",
    "Cooperative puzzles with portals and a humorous story.",
    "Fast action platforming with difficult boss battles.",
    "Turn-based strategy and building an empire.",
    "A short atmospheric adventure with an emotional story.",
    "Free multiplayer team combat.",
    "Exploration, secrets, and a hand-drawn world.",
]


def run_benchmark(cache_dir: Path, output: Path) -> int:
    import psutil

    process = psutil.Process()
    stop = threading.Event()
    samples = []

    def sample_memory():
        while not stop.is_set():
            samples.append(process.memory_info().rss)
            stop.wait(0.01)

    sampler = threading.Thread(target=sample_memory, daemon=True)
    sampler.start()
    try:
        import numpy as np
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        cache_dir.mkdir(parents=True, exist_ok=True)

        def download(filename):
            return hf_hub_download(MODEL, filename, revision=REVISION, cache_dir=str(cache_dir))

        tokenizer = Tokenizer.from_file(download("tokenizer.json"))
        tokenizer.enable_truncation(max_length=256)
        tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        paths = {name: download(name) for name in ("onnx/model.onnx", "onnx/model_quint8_avx2.onnx")}
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        outputs = {}
        runs = []
        for name, path in paths.items():
            started = time.perf_counter()
            session = ort.InferenceSession(path, sess_options=options, providers=["CPUExecutionProvider"])
            startup_ms = (time.perf_counter() - started) * 1000

            def encode(texts, inference_session):
                tokens = tokenizer.encode_batch(texts)
                inputs = {
                    "input_ids": np.array([item.ids for item in tokens], dtype=np.int64),
                    "attention_mask": np.array([item.attention_mask for item in tokens], dtype=np.int64),
                    "token_type_ids": np.array([item.type_ids for item in tokens], dtype=np.int64),
                }
                inputs = {item.name: inputs[item.name] for item in inference_session.get_inputs()}
                hidden = inference_session.run(None, inputs)[0]
                mask = inputs["attention_mask"][:, :, None].astype(np.float32)
                pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
                return pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9)

            outputs[name] = encode(TEXTS, session)
            if outputs[name].shape != (8, 384) or not np.isfinite(outputs[name]).all():
                raise ValueError("Unexpected embedding representation")
            timings = []
            for i in range(24):
                started = time.perf_counter()
                encode([TEXTS[i % len(TEXTS)]], session)
                timings.append((time.perf_counter() - started) * 1000)
            runs.append({"file": name, "bytes": Path(path).stat().st_size,
                         "startup_ms": round(startup_ms, 2), "warm_query_samples": len(timings),
                         "warm_query_p50_ms": round(float(np.percentile(timings, 50)), 2),
                         "warm_query_p95_ms": round(float(np.percentile(timings, 95)), 2),
                         "rss_after_requests_mb": round(process.memory_info().rss / 1024**2, 2)})
            del session
            gc.collect()
        cosines = (outputs["onnx/model.onnx"] * outputs["onnx/model_quint8_avx2.onnx"]).sum(axis=1)
        report = {
            "schema_version": 1, "measured_at": datetime.now(UTC).isoformat(),
            "model": MODEL, "revision": REVISION, "max_tokens": 256,
            "pooling": "attention-mask mean, L2 normalized", "dimensions": 384,
            "threads": 1, "provider": "CPUExecutionProvider",
            "machine": {"logical_cpus": psutil.cpu_count(), "ram_mb": round(psutil.virtual_memory().total / 1024**2)},
            "runs": runs, "peak_sampled_process_rss_mb": round(max(samples) / 1024**2, 2),
            "quantized_vs_float_cosines": [round(float(value), 6) for value in cosines],
            "limitations": ["Eight short texts; no relevance evaluation or long-query load test.",
                            "ONNX float comparison is not parity against offline Sentence Transformers/PyTorch.",
                            "This is a local spike, not full API startup, hosted latency, or target-machine evidence."],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"job": "encoder-benchmark", "status": "ok", "report": str(output)}))
        return 0
    finally:
        stop.set()
        sampler.join()
