"""R0 only: sanitized real configuration/catalog inventory and local encoder check.

Never calls a language model, reserves quota, changes configuration or writes SQL.
"""

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.catalog.contracts import MODEL_ID, MODEL_REVISION
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.db.readiness import probe_catalog
from game_discovery.retrieval.query import load_query_encoder


def inspect(tokenizer: str, model: str, artifact: str) -> dict:
    settings = Settings.from_environment()
    result = {
        "measured_at": datetime.now(UTC).isoformat(),
        "configuration": {
            "database_configured": bool(settings.database_url.get_secret_value()),
            "groq_key_configured": bool(settings.groq_api_key.get_secret_value()),
            "groq_model": settings.groq_model,
            "ai_enabled": settings.ai_enabled,
            "daily_calls": settings.ai_daily_calls,
            "daily_reserved_tokens": settings.ai_daily_tokens,
            "query_paths_configured": {key: bool(getattr(settings, key)) for key in
                ("query_tokenizer_path", "query_model_path", "query_artifact_path")},
        },
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "live_provider_calls": 0,
        "database_writes": 0,
    }
    engine = create_runtime_engine(settings.database_url)
    try:
        readiness = probe_catalog(settings.database_url, engine)
        result["catalog"] = asdict(readiness)
        if readiness.error_code and engine is not None:
            try:
                with engine.connect():
                    pass
            except Exception as error:
                message = str(error).lower()
                categories = {"dns": ("getaddrinfo", "resolve host", "name or service"),
                    "authentication": ("password authentication", "authentication failed"),
                    "timeout": ("timeout", "timed out"), "refused": ("refused",),
                    "paused_or_unavailable": ("tenant or user not found", "database is not available"),
                    "tls": ("ssl", "certificate")}
                result["connection_diagnostic"] = {"error_type": type(error).__name__,
                    "categories": [key for key, terms in categories.items() if any(t in message for t in terms)]}
        encoder = load_query_encoder(tokenizer, model, artifact)
        if encoder is None:
            raise RuntimeError("R0 explicit local encoder paths are required")
        vector = encoder("single-player exploration and satisfying combat")
        result["explicit_local_encoder"] = {
            "hash_and_manifest_checks": "passed", "dimensions": len(vector),
            "squared_norm": sum(x * x for x in vector), "artifact_version": encoder.catalog_version,
            "configured_in_application": all(result["configuration"]["query_paths_configured"].values()),
        }
        if readiness.error_code or engine is None:
            result["status"] = "blocked_catalog_connection"
            return result
        repo = CatalogRepository(engine)
        # An explicit inventory cap, not an unbounded production retrieval path.
        page = repo.search("", 256, 0)
        if page.total > 256 or page.catalog_version != readiness.version:
            raise RuntimeError("R0 inventory exceeds bound or active catalog changed")
        result["inventory"] = [{"app_id": g.app_id, "title": g.title, "modes": g.modes,
            "platforms": g.platforms, "price_cents": g.price.amount_cents if g.price else None,
            "free_to_play": g.free_to_play} for g in page.items]
        if encoder.catalog_version != page.catalog_version:
            raise RuntimeError("R0 verified model manifest differs from active catalog")
        # Existing discover() requires matching catalog version and the vector join.
        from game_discovery.catalog.contracts import DiscoverRequest

        version, games = repo.discover(DiscoverRequest(query="exploration", limit=4), vector, encoder.catalog_version)
        result["explicit_local_encoder"].update({
            "catalog_version": version,
            "existing_read_only_vector_query_ids": [g.game.app_id for g in games],
            "configured_in_application": all(result["configuration"]["query_paths_configured"].values()),
            "interpretation": "compatibility probe, not new hybrid retrieval or relevance evaluation",
        })
        result["status"] = "ok"
        return result
    finally:
        if engine is not None:
            engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = inspect(args.tokenizer, args.model, args.artifact)
    except Exception as error:
        # Database/driver exceptions can contain sensitive connection information.
        safe_reason = str(error) if isinstance(error, RuntimeError) and str(error).startswith("R0 ") else type(error).__name__
        raise SystemExit(f"R0 probe failed: {safe_reason}; no driver details logged") from None
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(args.output), "provider_calls": 0}))
    if result["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
