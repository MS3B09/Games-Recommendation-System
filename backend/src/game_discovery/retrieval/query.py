"""Bounded query encoding and lexical terms, with no request-time downloads."""

import math
import hashlib
import json
import re
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol


class QueryEncoder(Protocol):
    catalog_version: str

    def __call__(self, query: str) -> list[float]: ...


class QueryEncoderBusy(ValueError):
    """Typed local contention; callers can report fallback without parsing text."""


def validate_query_vector(vector: list[float]) -> None:
    if (len(vector) != 384 or not all(math.isfinite(value) for value in vector)
            or abs(sum(value * value for value in vector) - 1) > 0.001):
        raise ValueError("Invalid query embedding")


class BoundedQueryEncoder:
    """Serialize access to a shared tokenizer/session; fail open to lexical retrieval."""

    def __init__(self, encode: Callable[[str], list[float]], catalog_version: str):
        self.encode = encode
        self.catalog_version = catalog_version
        self.slot = threading.BoundedSemaphore(1)

    def __call__(self, query: str) -> list[float]:
        if not self.slot.acquire(blocking=False):
            raise QueryEncoderBusy("Query encoder is busy")
        try:
            vector = self.encode(query)
            validate_query_vector(vector)
            return vector
        finally:
            self.slot.release()


def load_query_encoder(tokenizer_path: str, model_path: str, artifact_path: str) -> QueryEncoder | None:
    if not all((tokenizer_path, model_path, artifact_path)):
        return None
    from game_discovery.catalog.contracts import MODEL_ID, MODEL_REVISION, digest
    from game_discovery.retrieval.encoder import OnnxEncoder

    artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    unsigned = {key: value for key, value in artifact.items() if key != "version"}
    if (artifact.get("model_id"), artifact.get("model_revision"), artifact.get("dimensions")) != (MODEL_ID, MODEL_REVISION, 384):
        raise ValueError("Query model does not match catalog representation")
    if artifact.get("version") != "m2-" + digest(unsigned)[:24]:
        raise ValueError("Invalid query artifact manifest")
    for path, key in ((tokenizer_path, "tokenizer_sha256"), (model_path, "model_sha256")):
        # Streaming avoids a second model-sized allocation on the 512 MB host.
        with Path(path).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != artifact.get(key):
                raise ValueError("Query model representation hash mismatch")
    encoder = OnnxEncoder(Path(tokenizer_path), Path(model_path))
    return BoundedQueryEncoder(lambda query: list(map(float, encoder.encode([query])[0])), artifact["version"])


def lexical_query(query: str) -> str:
    # OR lets short descriptions match some request words, rather than requiring
    # every word of a conversational request. Only generated alphabetic tokens
    # enter tsquery syntax; the resulting string is still a bound SQL parameter.
    terms = list(dict.fromkeys(re.findall(r"[a-zA-Z]{2,40}", query.casefold())))[:64]
    return " | ".join(terms)


def uncertainty(query: str) -> list[str]:
    if not query.strip():
        return []
    return [
        "Text similarity is a ranking signal, not verified evidence of difficulty, repetition, mood, or enjoyment.",
    ]
