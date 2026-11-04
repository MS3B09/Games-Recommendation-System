"""Opt-in PostgreSQL AI-budget checks in an isolated, cleaned-up scratch schema."""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from game_discovery.core.database_url import normalize_db_url
from game_discovery.jobs.catalog import write_json


def connection_url(env_file: Path, variable: str = "MIGRATION_DATABASE_URL") -> str:
    values = dotenv_values(env_file, interpolate=False)
    raw = os.environ.get(variable, values.get(variable) or "")
    if not raw:
        raise ValueError("Configure separate migration/runtime connections locally for scratch-schema verification")
    return make_url(normalize_db_url(raw)).set(drivername="postgresql").render_as_string(hide_password=False)


def reserve(url: str, schema: str, tokens: int = 1000, calls: int = 2, limit: int = 10000) -> bool:
    if not schema.startswith("m4_budget_verify_") or not schema.removeprefix("m4_budget_verify_").isalnum():
        raise ValueError("Invalid scratch-schema identity")
    with psycopg.connect(url, connect_timeout=5, prepare_threshold=None, options="-c statement_timeout=5000 -c lock_timeout=2000") as connection:
        if connection.execute("select current_user").fetchone()[0] != "game_discovery_runtime":
            raise ValueError("The budget verifier requires the restricted runtime login")
        try:
            return connection.execute(f'select "{schema}".reserve_ai_usage(%s,%s,%s)', (tokens, calls, limit)).fetchone()[0] is True
        except Exception as error:
            error.add_note("runtime_function_execute")
            raise


def verify(env_file: Path, output: Path) -> dict:
    url = connection_url(env_file)
    runtime_url = connection_url(env_file, "DATABASE_URL")
    schema = "m4_budget_verify_" + uuid4().hex[:16]
    migration = Path(__file__).resolve().parents[3] / "migrations" / "0004_ai_budget.sql"
    sql = migration.read_text(encoding="utf-8").replace("discovery.", f'"{schema}".')
    report = {"observed_at": datetime.now(UTC).isoformat(), "status": "failed", "schema": schema,
              "application_schema_changed": False, "cleanup": False, "checks": []}
    def stage(name: str) -> None:
        report["stage"] = name
        write_json(output, report)
        print(json.dumps({"stage": name}), flush=True)
    try:
        with psycopg.connect(url, connect_timeout=5, prepare_threshold=None, autocommit=True, options="-c statement_timeout=5000 -c lock_timeout=2000") as admin:
            stage("create_scratch_schema")
            admin.execute(f'create schema "{schema}"')
            stage("grant_scratch_usage")
            admin.execute(f'grant usage on schema "{schema}" to game_discovery_runtime')
            stage("apply_scratch_migration")
            admin.execute(sql)
            stage("upgrade_preserves_consumed_usage")
            admin.execute(f"insert into \"{schema}\".ai_usage_windows(id,day,calls,reserved_tokens,minute,minute_calls) values(true,(clock_timestamp() at time zone 'UTC')::date,20,100000,date_trunc('minute',clock_timestamp())-interval '2 minutes',4)")
            before = admin.execute(f'select * from "{schema}".ai_usage_windows').fetchone()
            upgrade = migration.with_name("0005_ai_budget_limits.sql").read_text(encoding="utf-8").replace("discovery.", f'"{schema}".')
            admin.execute(upgrade)
            assert admin.execute(f'select * from "{schema}".ai_usage_windows').fetchone() == before
            assert reserve(runtime_url, schema, tokens=1000, calls=50, limit=500000)
            assert admin.execute(f'select calls,reserved_tokens from "{schema}".ai_usage_windows').fetchone() == (21, 101000)
            report["checks"].append("new migration preserves usage and grants reservations above the old daily ceilings")
            stage("new_daily_ceiling_concurrency")
            admin.execute(f"update \"{schema}\".ai_usage_windows set calls=48,reserved_tokens=498000,minute=minute-interval '2 minutes',minute_calls=0")
            with ThreadPoolExecutor(max_workers=4) as executor:
                outcomes = list(executor.map(lambda _: reserve(runtime_url, schema, calls=50, limit=500000), range(4)))
            assert outcomes.count(True) == 2
            assert admin.execute(f'select calls,reserved_tokens from "{schema}".ai_usage_windows').fetchone() == (50, 500000)
            report["checks"].append("concurrent reservations stop at exactly 50 calls and 500000 reserved tokens")
            stage("new_daily_ceiling_validation")
            assert not reserve(runtime_url, schema, calls=51, limit=500000)
            assert not reserve(runtime_url, schema, calls=50, limit=500001)
            assert not reserve(runtime_url, schema, tokens=16001, calls=50, limit=500000)
            report["checks"].append("oversized daily ceilings and per-call reservations remain denied")
            admin.execute(f'delete from "{schema}".ai_usage_windows')
            stage("initial_token_limit")
            assert not reserve(runtime_url, schema, tokens=2000, limit=1000)
            assert admin.execute(f'select count(*) from "{schema}".ai_usage_windows').fetchone()[0] == 0
            report["checks"].append("initial reservation cannot exceed configured token limit")
            stage("concurrent_reservations")
            with ThreadPoolExecutor(max_workers=4) as executor:
                outcomes = list(executor.map(lambda _: reserve(runtime_url, schema), range(4)))
            assert outcomes.count(True) == 2
            assert admin.execute(f'select calls,reserved_tokens from "{schema}".ai_usage_windows').fetchone() == (2, 2000)
            report["checks"].append("four concurrent runtime calls grant exactly two reservations")
            stage("restart_probe")
            process = subprocess.run([sys.executable, "-m", "game_discovery.jobs.verify_ai_budget", "--env-file", str(env_file), "--probe-schema", schema],
                                     capture_output=True, timeout=30, check=False)
            assert process.returncode == 0
            report["checks"].append("new Python process cannot reset or exceed the consumed budget")
            stage("token_exhaustion")
            admin.execute(f'delete from "{schema}".ai_usage_windows')
            assert reserve(runtime_url, schema, tokens=1000, calls=20, limit=1500)
            assert not reserve(runtime_url, schema, tokens=1000, calls=20, limit=1500)
            report["checks"].append("token exhaustion denies subsequent reservations")
            stage("minute_exhaustion")
            admin.execute(f'delete from "{schema}".ai_usage_windows')
            assert sum(reserve(runtime_url, schema, calls=20) for _ in range(5)) == 4
            report["checks"].append("global four-calls-per-minute ceiling is enforced")
            stage("private_counters")
            with psycopg.connect(runtime_url, connect_timeout=5, prepare_threshold=None, options="-c statement_timeout=5000 -c lock_timeout=2000") as runtime:
                try:
                    runtime.execute(f'select * from "{schema}".ai_usage_windows')
                except psycopg.errors.InsufficientPrivilege:
                    report["checks"].append("runtime cannot read or reset private counters directly")
                else:
                    raise AssertionError("Runtime gained direct counter access")
            stage("window_rollover")
            admin.execute(f"update \"{schema}\".ai_usage_windows set day=day-1,minute=minute-interval '2 minutes',calls=50,reserved_tokens=500000,minute_calls=4")
            assert reserve(runtime_url, schema, calls=50, limit=500000)
            assert admin.execute(f'select calls,reserved_tokens,minute_calls from "{schema}".ai_usage_windows').fetchone() == (1, 1000, 1)
            report["checks"].append("database UTC window rollover reuses the single bounded row")
            stage("r4_upgrade_preserves_usage")
            admin.execute(f"update \"{schema}\".ai_usage_windows set calls=50,reserved_tokens=393494,minute=minute-interval '2 minutes',minute_calls=4")
            before_r4 = admin.execute(f'select * from "{schema}".ai_usage_windows').fetchone()
            r4_upgrade = migration.with_name("0006_r4_ai_budget_limits.sql").read_text(encoding="utf-8").replace("discovery.", f'"{schema}".')
            admin.execute(r4_upgrade)
            assert admin.execute(f'select * from "{schema}".ai_usage_windows').fetchone() == before_r4
            assert reserve(runtime_url, schema, calls=100, limit=1500000)
            assert admin.execute(f'select calls,reserved_tokens from "{schema}".ai_usage_windows').fetchone() == (51, 394494)
            report["checks"].append("R4 migration preserves all consumed counters; call 51 adds usage rather than resetting it")
            stage("r4_concurrent_ceiling")
            admin.execute(f"update \"{schema}\".ai_usage_windows set calls=98,reserved_tokens=1498000,minute=minute-interval '2 minutes',minute_calls=0")
            with ThreadPoolExecutor(max_workers=4) as executor:
                outcomes = list(executor.map(lambda _: reserve(runtime_url, schema, calls=100, limit=1500000), range(4)))
            assert outcomes.count(True) == 2
            assert admin.execute(f'select calls,reserved_tokens from "{schema}".ai_usage_windows').fetchone() == (100, 1500000)
            report["checks"].append("R4 concurrent reservations stop at exactly 100 calls and 1500000 reserved units")
            stage("r4_invalid_limits_and_restore")
            for tokens, calls, limit in ((1000, 101, 1500000), (1000, 100, 1500001), (16001, 100, 1500000), (1000, 50, 500000)):
                assert not reserve(runtime_url, schema, tokens=tokens, calls=calls, limit=limit)
            assert admin.execute(f'select calls,reserved_tokens from "{schema}".ai_usage_windows').fetchone() == (100, 1500000)
            report["checks"].append("R4 invalid ceilings/per-call bounds denied; restoring lower runtime limits retains counters")
            stage("r4_minute_guard")
            admin.execute(f"update \"{schema}\".ai_usage_windows set calls=1,reserved_tokens=1000,minute=date_trunc('minute',clock_timestamp()),minute_calls=4")
            assert not reserve(runtime_url, schema, calls=100, limit=1500000)
            report["checks"].append("expanded daily limits do not bypass the four-per-minute guard")
            stage("r4_utc_rollover")
            admin.execute(f"update \"{schema}\".ai_usage_windows set day=day-1,calls=100,reserved_tokens=1500000,minute=minute-interval '2 minutes',minute_calls=4")
            assert reserve(runtime_url, schema, calls=100, limit=1500000)
            assert admin.execute(f'select calls,reserved_tokens,minute_calls from "{schema}".ai_usage_windows').fetchone() == (1, 1000, 1)
            report["checks"].append("R4 next-UTC-day rollover still uses the same single row")
            report["status"] = "passed"
    except Exception as error:
        report["error_kind"] = type(error).__name__
        report["sqlstate"] = getattr(error, "sqlstate", None)
        report["operation"] = getattr(error, "__notes__", [])
        raise
    finally:
        with psycopg.connect(url, connect_timeout=5, prepare_threshold=None, autocommit=True, options="-c statement_timeout=5000 -c lock_timeout=2000") as admin:
            admin.execute(f'drop schema if exists "{schema}" cascade')
            report["cleanup"] = admin.execute("select to_regnamespace(%s) is null", (schema,)).fetchone()[0]
        write_json(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path("backend/.env"))
    parser.add_argument("--output", type=Path, default=Path("docs/reports/m4-budget-evidence.json"))
    parser.add_argument("--probe-schema", help=argparse.SUPPRESS)
    parser.add_argument("--cleanup-schema", help="Remove only a named scratch schema left by an interrupted verifier")
    args = parser.parse_args()
    try:
        if args.cleanup_schema:
            schema = args.cleanup_schema
            if not schema.startswith("m4_budget_verify_") or len(schema) != 33 or not schema.removeprefix("m4_budget_verify_").isalnum():
                raise ValueError("Refusing unrelated schema cleanup")
            with psycopg.connect(connection_url(args.env_file), connect_timeout=5, autocommit=True, options="-c statement_timeout=5000 -c lock_timeout=2000") as connection:
                connection.execute(f'drop schema if exists "{schema}" cascade')
                print(json.dumps({"cleanup": connection.execute("select to_regnamespace(%s) is null", (schema,)).fetchone()[0]}))
            return
        if args.probe_schema:
            if reserve(connection_url(args.env_file, "DATABASE_URL"), args.probe_schema):
                raise ValueError("Budget unexpectedly granted after process restart")
            return
        report = verify(args.env_file, args.output)
        print(json.dumps({"status": report["status"], "checks": len(report["checks"]), "cleanup": report["cleanup"]}))
    except Exception:
        parser.exit(1, "AI budget verification failed; no credentials or driver details are logged. Inspect the saved check report and local configuration.\n")


if __name__ == "__main__":
    main()
