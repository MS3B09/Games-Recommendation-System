"""Read-only audit of public synthetic v13-v21 journals; never calls a model."""
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    authority = Path('C:/Users/User/AppData/Local/Temp/opencode')
    names = ['llm-first-held-out-v13', *[f'llm-first-development-v{version}' for version in range(14, 21)],
             'llm-first-held-out-v20', 'llm-first-held-out-v21']
    report = {'at': datetime.now(UTC).isoformat(), 'kind': 'mixed_version_data_audit_not_quality_acceptance',
              'human_scores': None, 'journals': []}
    calls = units = tokens = unknown_usage = 0
    for name in names:
        path = authority / (name + '.json')
        if not path.is_file():
            continue
        raw = path.read_bytes()
        journal = json.loads(raw)
        turns = []
        case_results = []
        for case in journal['cases']:
            case_results.append({'id': case['id'], 'finished': case.get('finished', False),
                'synthetic_seed_turns': case.get('seed_turns', 0),
                'dependent_turns_skipped': case.get('dependent_turns_skipped', 0),
                'cleanup_status': case.get('cleanup_status')})
            for turn in case['turns']:
                traces = [trace for attempt in (turn.get('stored_event') or {}).get('attempts', [])
                          for trace in attempt['trace'] if 'model_call' in trace]
                for trace in traces:
                    calls += 1
                    units += trace.get('reserved_units') or 0
                    if trace.get('reported_usage') is None:
                        unknown_usage += 1
                    else:
                        tokens += trace['reported_usage'].get('total_tokens', 0)
                response = turn['response']
                turns.append({'case': case['id'], 'turn': turn['index'] + 1, 'status': turn['status'],
                    'message': response.get('message'), 'elapsed_ms': turn['elapsed_ms'],
                    'model_calls': len(traces), 'code': response.get('code'), 'retry_at': response.get('retry_at'),
                    'card_ids': [card['game']['app_id'] for card in response.get('games', [])],
                    'applied_filters': response.get('applied_filters'),
                    'preference_changes': response.get('preference_changes')})
        latencies = sorted(turn['elapsed_ms'] for turn in turns if turn['status'] == 200)
        report['journals'].append({'name': name, 'sha256': hashlib.sha256(raw).hexdigest(),
            'attempted': len(turns), 'http_200_deliveries': len(latencies), 'paused': journal.get('paused'),
            'delivered_http_p95_ms': latencies[math.ceil(len(latencies) * .95) - 1] if latencies else None,
            'cases': case_results, 'turns': turns})
    report['accounting'] = {'observed_reserved_model_calls': calls, 'reserved_units': units,
        'known_reported_tokens': tokens, 'calls_without_reported_usage': unknown_usage,
        'note': 'Reported tokens are incomplete and do not establish provider organization headroom.'}
    target = root / 'docs/reports/llm-first-resume-2026-10-30.json'
    assert target.parent.is_dir()
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(target), 'accounting': report['accounting'], 'journals': [
        {key: row[key] for key in ('name', 'attempted', 'http_200_deliveries', 'delivered_http_p95_ms')}
        for row in report['journals']]}))


if __name__ == '__main__':
    main()
