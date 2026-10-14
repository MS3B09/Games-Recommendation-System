"""Streaming legacy CSV audit. Disk-backed counters bound memory as catalogs grow."""

import csv
import hashlib
import json
import re
import sqlite3
import tempfile
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

MISSING = {"", "unknown", "n/a", "nan", "null", "none", "[]", "['[]']", "['unknown']"}
APP_PATH = re.compile(r"^/app/([1-9][0-9]*)(?:/|$)")
SUSPICIOUS = re.compile(r"\b(soundtrack|dlc|demo|dedicated server|software)\b", re.I)
SEEDS = ("Hades", "Stardew Valley", "Portal 2", "Hollow Knight", "Dead Cells", "Celeste")


def steam_app_id(url: str) -> int | None:
    """Only accept identity from a Steam store app URL, never artwork/title guesses."""
    try:
        parsed = urlsplit(url.strip())
        if parsed.scheme not in {"http", "https"}:
            return None
        if parsed.hostname != "store.steampowered.com" or parsed.port is not None:
            return None
        match = APP_PATH.match(parsed.path)
        return int(match[1]) if match else None
    except ValueError:
        return None


def missing(value: str | None) -> bool:
    return value is None or value.strip().casefold() in MISSING


def audit_csv(path: Path) -> dict:
    started = time.perf_counter()
    # Hash without holding the file in memory. Import time is never observation time.
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    csv.field_size_limit(16 * 1024 * 1024)
    absent = Counter()
    invalid_platforms = Counter()
    platform_values = {key: Counter() for key in ("Windows", "macOS", "Linux", "SteamOS")}
    seed_rows = {seed: [] for seed in SEEDS}
    rows = malformed = ids_missing = suspicious = 0
    suspicious_examples = []
    max_description = 0
    # Distinct hashes/identities/titles are kept on disk, not a growing Python set.
    with tempfile.TemporaryDirectory(prefix="game-audit-") as directory:
        db = sqlite3.connect(str(Path(directory) / "counts.sqlite"))
        try:
            db.execute("PRAGMA cache_size = -2048")
            db.execute("CREATE TABLE counts (kind TEXT, value TEXT, n INTEGER, PRIMARY KEY(kind,value))")
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                headers = reader.fieldnames
                if not headers or len(set(headers)) != len(headers):
                    raise ValueError("CSV requires unique column headers")
                for row in reader:
                    rows += 1
                    if None in row or any(value is None for value in row.values()):
                        malformed += 1
                        continue
                    for key in headers:
                        if missing(row[key]):
                            absent[key] += 1
                    app_id = steam_app_id(row.get("Link", ""))
                    ids_missing += app_id is None
                    title = row.get("title", "").strip()
                    # Exclude legacy dataframe index when identifying duplicate content.
                    content = {k: v for k, v in row.items() if k and not k.startswith("Unnamed:")}
                    content_hash = hashlib.sha256(
                        json.dumps(content, sort_keys=True, ensure_ascii=False).encode()
                    ).hexdigest()
                    for kind, value in (("id", str(app_id) if app_id else ""),
                                        ("title", title.casefold()), ("row", content_hash)):
                        if value:
                            db.execute(
                                "INSERT INTO counts VALUES (?, ?, 1) ON CONFLICT(kind,value) "
                                "DO UPDATE SET n=n+1", (kind, value)
                            )
                    for key, values in platform_values.items():
                        if key in row:
                            value = row[key].strip().casefold()
                            values[value if value in {"0", "1", "true", "false"} else "unknown_or_invalid"] += 1
                            if not missing(value) and value not in {"0", "1", "true", "false"}:
                                invalid_platforms[key] += 1
                    max_description = max(max_description, len(row.get("about_game", "")))
                    if SUSPICIOUS.search(title):
                        suspicious += 1
                        if len(suspicious_examples) < 10:
                            suspicious_examples.append({"title": title, "app_id": app_id})
                    for seed in SEEDS:
                        if title.casefold() == seed.casefold() and len(seed_rows[seed]) < 5:
                            seed_rows[seed].append({"app_id": app_id, "row_number": rows})
                    if rows % 1000 == 0:
                        db.commit()
            distinct = {}
            duplicates = {}
            for kind in ("id", "title", "row"):
                distinct[kind] = db.execute("SELECT COUNT(*) FROM counts WHERE kind=?", (kind,)).fetchone()[0]
                duplicates[kind] = db.execute(
                    "SELECT COALESCE(SUM(n-1),0) FROM counts WHERE kind=?", (kind,)
                ).fetchone()[0]
        finally:
            db.close()
    return {
        "input": path.name, "sha256": digest, "bytes": path.stat().st_size,
        "encoding": "utf-8-sig (strict decode)", "headers": headers,
        "rows": rows, "malformed_rows": malformed,
        "missing_by_column": {key: absent[key] for key in headers},
        "distinct": distinct, "duplicate_excess_rows": duplicates,
        "missing_or_invalid_store_app_id": ids_missing,
        "platform_values": platform_values, "invalid_platform_values": dict(invalid_platforms),
        "max_description_characters": max_description,
        "suspected_non_game_title_count": suspicious,
        "suspected_non_game_examples": suspicious_examples,
        "seed_coverage": seed_rows,
        "provenance": {"collection_timestamp": None, "price_currency": None,
                       "price_region": None, "note": "Legacy fields are unaudited observations; title heuristics are not eligibility classifications."},
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }


def run_audit(inputs: list[Path], output: Path) -> dict:
    report = {"schema_version": 1, "audited_at": datetime.now(UTC).isoformat(),
              "datasets": [audit_csv(path) for path in inputs]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
