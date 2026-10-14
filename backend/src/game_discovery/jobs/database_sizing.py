"""Atomic, bounded private-schema sizing experiment, never catalog activation."""

import csv
import hashlib
import json
import math
import random
import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from itertools import islice
from pathlib import Path

from game_discovery.jobs.audit import missing, steam_app_id
from game_discovery.jobs.environment_check import db_url_matches_project, normalize_db_url

TABLES = ("runs", "games", "platforms", "terms", "game_terms", "prices", "reviews", "sources", "evidence", "embeddings")
FIELDS = ("title", "about_game", "genre", "developer", "publisher", "tags")
RUN_KEY = "m0-storage-v1"


def fixture_vector(app_id: int) -> str:
    """Deterministic unit vector for payload sizing, NOT a semantic embedding."""
    rng = random.Random(app_id)
    values = [rng.uniform(-1, 1) for _ in range(384)]
    norm = math.sqrt(sum(value * value for value in values))
    return "[" + ",".join(f"{value / norm:.8f}" for value in values) + "]"


def recorded_cents(value: str) -> int | None:
    try:
        amount = Decimal(value)
        cents = amount * 100
        if not amount.is_finite() or amount < 0 or cents != cents.to_integral_value() or cents > 2_147_483_647:
            return None
        return int(cents)
    except InvalidOperation:
        return None


def sample_rows(path: Path, limit: int):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in islice(csv.DictReader(stream), limit):
            app_id = steam_app_id(row.get("Link", ""))
            if app_id is None or None in row or any(value is None for value in row.values()):
                raise ValueError("Invalid legacy identity or malformed sizing input")
            yield app_id, row


def content_hash(row: dict) -> str:
    return hashlib.sha256((row["title"] + "\n" + row.get("about_game", "")[:12000]).encode()).hexdigest()


def run_sizing(path: Path, limit: int, env_file: Path, project_url: str, output: Path) -> int:
    import psycopg
    from dotenv import dotenv_values

    if not 1 <= limit <= 3000:
        raise ValueError("Sizing sample must be between 1 and 3000")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    config = dotenv_values(env_file, interpolate=False)
    url = config.get("MIGRATION_DATABASE_URL")
    if not db_url_matches_project(url, project_url):
        raise ValueError("Missing or mismatched migration database")
    started = time.perf_counter()
    try:
        with psycopg.connect(normalize_db_url(url), connect_timeout=10, prepare_threshold=None) as connection:
            connection.execute("SET LOCAL statement_timeout = '180s'")
            baseline = connection.execute("select pg_database_size(current_database())").fetchone()[0]
            if baseline + 128 * 1024**2 > 350_000_000:
                raise ValueError("Insufficient database sizing headroom")
            connection.execute("select pg_advisory_xact_lock(71313001)")
            existing = connection.execute(
                "select input_sha256, sample_limit from discovery_m0.runs where run_key=%s", (RUN_KEY,)
            ).fetchone()
            reused = existing is not None
            if existing and existing != (digest, limit):
                raise ValueError("Existing sizing experiment differs; refusing to overwrite it")
            if not reused:
                connection.execute("insert into discovery_m0.runs values (%s,%s,%s,now(),%s)",
                                   (RUN_KEY, digest, limit, "storage_experiment_only"))
                # COPY FROM STDIN is client-streamed; never read a database-server file.
                print(json.dumps({"job": "database-sizing", "phase": "copy_games"}), flush=True)
                with connection.cursor().copy("COPY discovery_m0.games (app_id,run_key,title,normalized_title,description,store_url,artwork_url,content_hash,eligibility,observed_at) FROM STDIN") as copy:
                    for app_id, row in sample_rows(path, limit):
                        copy.write_row((app_id, RUN_KEY, row["title"], row["title"].casefold(),
                                        row.get("about_game", "")[:12000], row["Link"], row.get("image"),
                                        content_hash(row), "quarantined", None))
                with connection.cursor().copy("COPY discovery_m0.terms FROM STDIN") as copy:
                    for term in range(1000):
                        copy.write_row((f"sizing-tag-{term}", "tag", f"Synthetic sizing tag {term}", "synthetic_storage_fixture"))
                for table in ("platforms", "game_terms", "prices", "reviews", "sources", "evidence", "embeddings"):
                    print(json.dumps({"job": "database-sizing", "phase": f"copy_{table}"}), flush=True)
                    columns = " (app_id,model_revision,content_hash,embedding)" if table == "embeddings" else ""
                    with connection.cursor().copy(f"COPY discovery_m0.{table}{columns} FROM STDIN") as copy:
                        for app_id, row in sample_rows(path, limit):
                            if table == "platforms":
                                for platform in ("windows", "macos", "linux"):
                                    copy.write_row((app_id, platform, None))
                            elif table == "game_terms":
                                for term in range(12):
                                    copy.write_row((app_id, f"sizing-tag-{(app_id + term) % 1000}"))
                            elif table == "prices":
                                copy.write_row((app_id, recorded_cents(row.get("Discount Price", "")), None, None, None, None))
                            elif table == "reviews":
                                count = recorded_cents(row.get("review_count", ""))
                                copy.write_row((app_id, None, count // 100 if count is not None else None,
                                                None if missing(row.get("review_type")) else row["review_type"], None))
                            elif table == "sources":
                                copy.write_row((app_id, row["Link"], None, digest))
                            elif table == "evidence":
                                for field in FIELDS:
                                    copy.write_row((app_id, field, row.get(field, "")[:512]))
                            else:
                                copy.write_row((app_id, "synthetic-storage-vector-v1", content_hash(row), fixture_vector(app_id)))
            counts = {table: connection.execute(f"select count(*) from discovery_m0.{table}").fetchone()[0] for table in TABLES}
            games = counts["games"]
            if games == 0 or counts["embeddings"] != games or counts["platforms"] != games * 3 or counts["evidence"] != games * 6 or counts["game_terms"] != games * 12:
                raise ValueError("Sizing import validation failed")
            if connection.execute("select count(*) from discovery_m0.games where eligibility <> 'quarantined'").fetchone()[0]:
                raise ValueError("Sizing records must never be eligible")
            sizes = connection.execute(
                "select c.relname, pg_table_size(c.oid), pg_indexes_size(c.oid), pg_total_relation_size(c.oid) "
                "from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                "where n.nspname='discovery_m0' and c.relkind='r' order by c.relname"
            ).fetchall()
            private = connection.execute("select not has_schema_privilege('anon','discovery_m0','usage') and not has_schema_privilege('authenticated','discovery_m0','usage')").fetchone()[0]
            if not private:
                raise ValueError("Sizing schema is not private")
            # Exercise an interrupted attempt: savepoint rollback preserves row count.
            with connection.transaction(force_rollback=True):
                connection.execute("insert into discovery_m0.terms values ('rollback-probe','tag','Interrupted fixture','synthetic_storage_fixture')")
            rollback_ok = connection.execute("select count(*) from discovery_m0.terms where term_key='rollback-probe'").fetchone()[0] == 0
            vector = fixture_vector(next(sample_rows(path, limit))[0])
            timings = []
            for _ in range(12):
                query_started = time.perf_counter()
                connection.execute(
                    "select app_id from discovery_m0.embeddings order by embedding OPERATOR(extensions.<=>) %s::extensions.vector, app_id limit 20", (vector,)
                ).fetchall()
                timings.append((time.perf_counter() - query_started) * 1000)
        # Commit complete experiment before measuring database total from a new transaction.
        with psycopg.connect(normalize_db_url(url), connect_timeout=10, prepare_threshold=None) as connection:
            connection.read_only = True
            connection.execute("SET LOCAL statement_timeout = '5s'")
            total_database = connection.execute("select pg_database_size(current_database())").fetchone()[0]
        total_relations = sum(row[3] for row in sizes)
        bytes_per_game = total_relations / games
        report = {
            "schema_version": 1, "measured_at": datetime.now(UTC).isoformat(), "input_sha256": digest,
            "sample_rows": games, "requested_limit": limit, "reused_complete_import": reused,
            "counts": counts, "relations": [{"table": name, "table_and_toast_bytes": table_size, "index_bytes": indexes, "total_bytes": total} for name, table_size, indexes, total in sizes],
            "database_bytes": total_database, "sample_total_relation_bytes": total_relations,
            "database_bytes_before_run": baseline,
            "bytes_per_game_including_sample_indexes": round(bytes_per_game, 2),
            "projection": {str(size): {"single_generation_bytes": math.ceil(bytes_per_game * size),
                                      "active_plus_staging_with_30_percent_margin_bytes": math.ceil(bytes_per_game * size * 2 * 1.3) + 32 * 1024**2,
                                      "below_350_mb_target": math.ceil(bytes_per_game * size * 2 * 1.3) + 32 * 1024**2 < 350_000_000}
                           for size in (6000, 8000, 10000)},
            "exact_vector_round_trip_ms": {"samples": 12, "p50": round(sorted(timings)[5], 2), "p95": round(sorted(timings)[-1], 2)},
            "private_schema_check": private, "interrupted_transaction_rollback_check": rollback_ok,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "limitations": ["Historical descriptions; synthetic taxonomy and unit vectors are storage fixtures, not recommendations.",
                            "Unknown currency/region/platform/freshness preserved; no catalog activated.",
                            "Projection is linear with margin, not a measured final schema or hosted load test.",
                            "Exact-search latency includes local-to-Supabase round trip and synthetic vectors."],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"job": "database-sizing", "status": "ok", "sample_rows": games, "report": str(output)}))
        return 0
    except psycopg.Error as error:
        print(json.dumps({"job": "database-sizing", "status": "failed", "error_type": type(error).__name__}))
        return 1
