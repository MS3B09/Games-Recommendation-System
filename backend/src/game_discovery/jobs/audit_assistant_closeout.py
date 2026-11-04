"""Export immutable public closeout snapshots and audit usage, never quality-rate.

Reads only explicitly named public C: journals. Private capabilities are neither
read nor exported. Source mismatches are reported, never repaired.
"""
import argparse
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path


def public_only(value):
    if isinstance(value, dict):
        if {'token', 'secret', 'secret_hash', 'groq_api_key', 'database_url'} & value.keys():
            raise ValueError('Private data must not enter public evaluation evidence')
        for child in value.values():
            public_only(child)
    elif isinstance(value, list):
        for child in value:
            public_only(child)


def token_bound(trace):
    """Known reported total, or the original reservation for missing usage."""
    usage = trace.get('reported_usage')
    total = usage.get('total_tokens') if isinstance(usage, dict) else None
    if type(total) is int and total >= 0:
        return total, 0, False
    reserved = trace.get('reserved_units')
    if reserved is None:
        reserved = 0
    if type(reserved) is not int or reserved < 0:
        raise ValueError('Invalid reservation cannot establish a token bound')
    return 0, reserved, True


def main() -> None:
    from game_discovery.core.settings import Settings
    from game_discovery.jobs.evaluate_dialogue_live import identity, quota_receipt

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journals', nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    authority = Path('C:/Users/User/AppData/Local/Temp/opencode')
    reports = root / 'docs/reports'
    if args.output.parent.resolve() != reports.resolve() or args.output.exists():
        parser.error('Use a fresh report filename in docs/reports')
    if len(set(args.journals)) != len(args.journals):
        parser.error('Duplicate journal names would double-count usage')
    report = {'at': datetime.now(UTC).isoformat(), 'human_scores': None, 'journals': []}
    calls = units = tokens = missing_usage = missing_units = 0
    turn_days = set()
    for name in args.journals:
        if (Path(name).name != name or not name.startswith('assistant-closeout-')
                or '.private' in name or not name.endswith('.json')):
            parser.error('Explicit public assistant-closeout journal basenames only')
        path = authority / name
        raw = path.read_bytes()
        journal = json.loads(raw)
        public_only(journal)
        digest = hashlib.sha256(raw).hexdigest()
        target = reports / f'{path.stem}-snapshot-{digest[:12]}.json'
        if target.exists() and target.read_bytes() != raw:
            raise RuntimeError('Snapshot differs; preserve and investigate')
        if not target.exists():
            target.write_bytes(raw)
        assert target.read_bytes() == raw
        fixture = next(p for p in reversed(journal['source_identity']) if p.startswith('data/evaluation/'))
        results = []
        for case in journal['cases']:
            for turn in case['turns']:
                turn_days.add(turn['at'][:10])
                traces = [trace for attempt in (turn.get('stored_event') or {}).get('attempts', [])
                          for trace in attempt['trace'] if 'model_call' in trace]
                for trace in traces:
                    calls += int(bool(trace.get('reserved_units')))
                    units += trace.get('reserved_units') or 0
                    reported, fallback, missing = token_bound(trace)
                    tokens += reported
                    missing_units += fallback
                    missing_usage += int(missing)
                response = turn.get('response') or {}
                tools = [trace for attempt in (turn.get('stored_event') or {}).get('attempts', [])
                         for trace in attempt['trace'] if 'tool' in trace]
                results.append({'case': case['id'], 'turn': turn['index'] + 1, 'status': turn['status'],
                    'message': response.get('message'), 'elapsed_ms': turn.get('elapsed_ms'),
                    'games': [{'id': card['game']['app_id'], 'title': card['game']['title'],
                               'price': card['game']['price']} for card in response.get('games', [])],
                    'model_calls': len(traces), 'applied_filters': response.get('applied_filters'),
                    'preference_changes': response.get('preference_changes'),
                    'tool_deliveries': [{'tool': trace['tool'],
                        'result_bytes': len(json.dumps(trace.get('result'), ensure_ascii=False,
                                                       separators=(',', ':')).encode()),
                        'error': (trace.get('delivered') or {}).get('error'),
                        'returned': (trace.get('delivered') or {}).get('returned')}
                        for trace in tools],
                    'code': response.get('code'), 'retry_at': response.get('retry_at')})
        times = sorted(t['elapsed_ms'] for t in results if t['status'] == 200)
        report['journals'].append({'source': str(path), 'snapshot': target.name, 'sha256': digest,
            'current_source_matches': identity(root, root / fixture) == journal['source_identity'],
            'attempted': len(results), 'http_200_deliveries': len(times),
            'http_p95_ms': times[math.ceil(len(times) * .95) - 1] if times else None,
            'paused': journal.get('paused'), 'cases': [{k: v for k, v in case.items() if k != 'turns'}
                                                    for case in journal['cases']], 'turns': results})
    settings = Settings.from_environment()
    report['receipt'] = quota_receipt(root, settings.ai_daily_calls, settings.ai_daily_tokens)
    report['accounting'] = {'observed_reserved_calls': calls, 'reserved_units': units,
                            'known_reported_tokens': tokens, 'traces_without_usage': missing_usage,
                            'unreported_reserved_units': missing_units,
                            'owned_reported_plus_missing_bound': tokens + missing_units,
                            'turn_start_days': sorted(turn_days),
                            'note': 'Aggregate owned usage/bound, not provider remaining balance. Cached tokens may reduce actual debit. Check applicable windows separately.'}
    with args.output.open('x', encoding='utf-8') as output:
        output.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'report': str(args.output), 'accounting': report['accounting'], 'receipt': report['receipt'],
        'journals': [{k: j[k] for k in ('sha256', 'attempted', 'http_200_deliveries', 'current_source_matches')}
                     for j in report['journals']]}))


if __name__ == '__main__':
    main()
