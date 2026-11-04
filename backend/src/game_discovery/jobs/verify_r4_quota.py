"""Verify applied R4 quotas with a real runtime reservation rolled back, no inference."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from game_discovery.core.settings import Settings
from game_discovery.jobs.evaluate_chat import save
from game_discovery.jobs.verify_ai_budget import connection_url


def verify(env_file):
    settings = Settings.from_environment()
    if (settings.ai_daily_calls, settings.ai_daily_tokens) != (100, 1500000):
        raise ValueError("temporary_r4_runtime_settings_required")
    report = {"observed_at": datetime.now(UTC).isoformat(), "runtime_limits": [100, 1500000],
              "normal_defaults": [Settings().ai_daily_calls, Settings().ai_daily_tokens],
              "provider_calls": 0, "committed_application_reservations": 0}
    with psycopg.connect(connection_url(env_file), connect_timeout=5, prepare_threshold=None) as admin:
        before = admin.execute("select row_to_json(w) from discovery.ai_usage_windows w").fetchone()[0]
        version = admin.execute("select version_num from discovery_migrations.alembic_version").fetchone()[0]
    if version != "0005":
        raise ValueError("r4_migration_not_applied")
    with psycopg.connect(connection_url(env_file, "DATABASE_URL"), connect_timeout=5, prepare_threshold=None) as runtime:
        if runtime.execute("select current_user").fetchone()[0] != "game_discovery_runtime":
            raise ValueError("restricted_runtime_required")
        try:
            granted = runtime.execute("select discovery.reserve_ai_usage(1000,100,1500000)").fetchone()[0]
            if granted is not True:
                raise ValueError("runtime_reservation_probe_denied")
        finally:
            runtime.rollback()
    with psycopg.connect(connection_url(env_file), connect_timeout=5, prepare_threshold=None) as admin:
        after = admin.execute("select row_to_json(w) from discovery.ai_usage_windows w").fetchone()[0]
    if after != before:
        raise ValueError("usage_changed_during_rollback_probe")
    report.update(status="passed", alembic_version=version, usage_before=before, usage_after=after,
                  reservation_granted_then_rolled_back=True, consumed_usage_unchanged=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path("backend/.env"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("new_output_in_existing_parent_required")
    try:
        report = verify(args.env_file)
        save(args.output, report)
        print(json.dumps(report))
    except Exception as error:
        parser.exit(1, json.dumps({"status": "failed", "error_type": type(error).__name__, "detail": "no_credentials_logged"}) + "\n")


if __name__ == "__main__":
    main()
