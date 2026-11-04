"""Opt-in isolated reservation-reason checks. No inference or app-counter writes."""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg
from game_discovery.jobs.verify_ai_budget import connection_url


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    migrations = root / 'backend/migrations'
    admin_url = connection_url(root / 'backend/.env')
    runtime_url = connection_url(root / 'backend/.env', 'DATABASE_URL')
    schema = 'error_budget_verify_' + uuid4().hex[:12]
    checks = []
    report = {'checks': checks, 'application_counters_changed': False, 'inference_calls': 0, 'cleanup': False}
    def reserve(tokens=1000, calls=100, units=1500000):
        with psycopg.connect(runtime_url, connect_timeout=5, prepare_threshold=None, options='-c statement_timeout=5000 -c lock_timeout=3000') as connection:
            return connection.execute(f'select * from "{schema}".reserve_ai_usage_detailed(%s,%s,%s)', (tokens, calls, units)).fetchone()
    with psycopg.connect(admin_url, connect_timeout=5, prepare_threshold=None, autocommit=True) as admin:
        before_app = admin.execute('select row_to_json(w) from discovery.ai_usage_windows w').fetchone()
        try:
            admin.execute(f'create schema "{schema}"')
            admin.execute(f'grant usage on schema "{schema}" to game_discovery_runtime')
            for filename in ('0004_ai_budget.sql', '0005_ai_budget_limits.sql', '0006_r4_ai_budget_limits.sql', '0007_ai_budget_error_reasons.sql'):
                admin.execute((migrations / filename).read_text(encoding='utf-8').replace('discovery.', f'"{schema}".'))
            assert reserve()[:2] == (True, 'granted')
            checks.append('initial reservation increments the same singleton')
            admin.execute(f"update \"{schema}\".ai_usage_windows set calls=100,reserved_tokens=813332,minute=minute-interval '2 minutes'")
            prior = admin.execute(f'select * from "{schema}".ai_usage_windows').fetchone()
            denied = reserve()
            assert denied[:2] == (False, 'daily_calls') and denied[2].hour == 0 and denied[2].tzinfo is not None
            assert admin.execute(f'select * from "{schema}".ai_usage_windows').fetchone() == prior
            checks.append('daily call denial has UTC reset and preserves every counter')
            admin.execute(f'update "{schema}".ai_usage_windows set calls=1,reserved_tokens=1499500')
            assert reserve()[:2] == (False, 'daily_units')
            checks.append('reserved-unit exhaustion distinguished from calls')
            admin.execute(f"update \"{schema}\".ai_usage_windows set reserved_tokens=1000,minute=date_trunc('minute',clock_timestamp()),minute_calls=4")
            assert reserve()[:2] == (False, 'minute_limit')
            checks.append('four-per-minute guard returns actual next-minute boundary')
            assert reserve(tokens=16001)[:2] == (False, 'invalid_limits')
            assert reserve(calls=101)[:2] == (False, 'invalid_limits')
            checks.append('invalid limits are not reported as exhausted allowance')
            admin.execute(f"update \"{schema}\".ai_usage_windows set calls=98,reserved_tokens=1498000,minute=minute-interval '2 minutes',minute_calls=0")
            with ThreadPoolExecutor(max_workers=4) as pool:
                outcomes = list(pool.map(lambda _: reserve(), range(4)))
            assert sum(row[0] for row in outcomes) == 2
            assert all(row[1] == 'daily_calls' for row in outcomes if not row[0])
            assert admin.execute(f'select calls,reserved_tokens from "{schema}".ai_usage_windows').fetchone() == (100, 1500000)
            checks.append('concurrent callers grant exactly two remaining calls; denial reasons stay correct')
            assert reserve(calls=50, units=500000)[:2] == (False, 'daily_calls')
            checks.append('restoring lower runtime ceilings never clears used counters')
            admin.execute(f"update \"{schema}\".ai_usage_windows set day=day-1,minute=minute-interval '2 minutes'")
            assert reserve()[0]
            assert admin.execute(f'select calls,reserved_tokens,minute_calls from "{schema}".ai_usage_windows').fetchone() == (1, 1000, 1)
            checks.append('normal next-day rollover remains atomic')
            with psycopg.connect(runtime_url, connect_timeout=5, prepare_threshold=None) as runtime:
                assert runtime.execute(f'select "{schema}".reserve_ai_usage(1000,100,1500000)').fetchone()[0]
            assert admin.execute(f'select calls from "{schema}".ai_usage_windows').fetchone()[0] == 2
            checks.append('legacy boolean function and detailed function share usage')
            with psycopg.connect(runtime_url, connect_timeout=5, prepare_threshold=None) as runtime:
                try:
                    runtime.execute(f'select * from "{schema}".ai_usage_windows')
                except psycopg.errors.InsufficientPrivilege:
                    checks.append('runtime remains unable to read or reset private counters')
                else:
                    raise AssertionError('direct counter access')
            assert admin.execute('select row_to_json(w) from discovery.ai_usage_windows w').fetchone() == before_app
            report['status'] = 'passed'
        finally:
            admin.execute(f'drop schema if exists "{schema}" cascade')
            report['cleanup'] = admin.execute('select to_regnamespace(%s) is null', (schema,)).fetchone()[0]
            report['observed_at'] = datetime.now(UTC).isoformat()
            (root / 'docs/reports/error-handling-budget-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
