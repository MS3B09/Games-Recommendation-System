"""Versioned, append-only live conversations through actual HTTP/accounting.

No failed-turn replay or automatic provider retry. Capabilities stay in approved
private C: storage; public reports contain only synthetic evaluation transcripts.
"""
import argparse
import hashlib
import json
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


def post(path: str, data: dict) -> tuple[int, dict]:
    request = Request('http://127.0.0.1:8001' + path, json.dumps(data).encode(), {'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=75) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)
    except (URLError, TimeoutError):
        return 0, {'code': 'transport_failure'}


def identity(root: Path, cases_path: Path | None = None) -> dict:
    paths = [root / 'data/evaluation/dialogue-v1.json', *sorted((root / 'backend/src/game_discovery/ai').glob('*.py')),
             root / 'backend/migrations/0008_conversation_archive.sql',
             root / 'backend/migrations/0009_archive_bootstrap_capacity.sql',
             root / 'backend/src/game_discovery/api/conversation_routes.py',
             root / 'backend/src/game_discovery/catalog/repository.py', Path(__file__)]
    if cases_path is not None and cases_path not in paths:
        paths.append(cases_path)
    for package in ('api', 'catalog', 'retrieval', 'core', 'db'):
        paths.extend(path for path in sorted((root / 'backend/src/game_discovery' / package).glob('*.py')) if path not in paths)
    return {str(path.relative_to(root)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def save(path: Path, value: dict) -> None:
    assert path.parent.is_dir()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def wait_for_window(journal: dict) -> None:
    sidecar = Path('C:/Users/User/AppData/Local/Temp/opencode/llm-first-last-attempt.json')
    stamps = [journal.get('last_attempt_at')]
    if sidecar.exists():
        stamps.append(json.loads(sidecar.read_text(encoding='utf-8')).get('at'))
    known = [datetime.fromisoformat(stamp) for stamp in stamps if stamp]
    if known:
        delay = 61 - (datetime.now(UTC) - max(known)).total_seconds()
        if delay > 0:
            time.sleep(delay)


def quota_receipt(root: Path, calls: int, units: int) -> dict:
    import psycopg
    from game_discovery.jobs.verify_ai_budget import connection_url
    with psycopg.connect(connection_url(root / 'backend/.env'), connect_timeout=5, prepare_threshold=None) as connection:
        connection.execute('set transaction read only')
        row = connection.execute("select current_timestamp,day,calls,reserved_tokens,(clock_timestamp() at time zone 'UTC')::date from discovery.ai_usage_windows").fetchone()
    effective_calls = row[2] if row[1] == row[4] else 0
    effective_units = row[3] if row[1] == row[4] else 0
    return {'at': row[0].isoformat(), 'day': row[4].isoformat(), 'effective_calls': effective_calls,
            'effective_units': effective_units, 'remaining_calls': calls-effective_calls, 'remaining_units': units-effective_units}


def seed_long(key: dict, private: dict, path: Path, spec: dict | None = None) -> None:
    from game_discovery.ai.conversation_store import ConversationKey, ConversationStore, ConversationTurn
    from game_discovery.catalog.repository import CatalogRepository
    from game_discovery.core.settings import Settings
    from game_discovery.db.engine import create_runtime_engine
    engine = create_runtime_engine(Settings.from_environment().database_url)
    store = ConversationStore(engine)
    spec = spec or {}
    games = CatalogRepository(engine).resolve(spec.get('game_ids', [1145360, 646570])).items
    try:
        seeds = private.setdefault('seed_ids', [str(uuid4()) for _ in range(80)])
        save(path, private)
        for index, rid in enumerate(seeds):
            snapshot = store.read(ConversationKey(**key))
            if any(e['id'] == rid and e['status'] == 'done' for e in snapshot['document']['events']):
                continue
            message = (spec.get('initial', 'I use Linux; my friend is Noor; we plan to play on Saturday. Please remember that.') if index == 0 else
                       spec.get('correction', 'Change the plan to Sunday. My friend is still Noor. Do not assume a budget.') if index == 40 else
                       'Let us discuss ' + ' and '.join(g.title for g in games) + '.' if index == 8 else
                       f'An unrelated conversational exchange numbered {index}.')
            turn = ConversationTurn(**key, turn_id=rid, revision=snapshot['revision'], message=message)
            started = store.begin(turn)
            memory = started['document']['memory']
            if index == 0:
                memory.update({name: {'value': value, 'source_turn': rid, 'revision': index+1}
                               for name, value in spec.get('initial_memory', {'platform': 'Linux', 'friend': 'Noor', 'plan_day': 'Saturday'}).items()})
            if index == 40:
                memory.update({name: {'value': value, 'source_turn': rid, 'revision': index+1}
                               for name, value in spec.get('corrected_memory', {'plan_day': 'Sunday', 'budget': 'Unspecified; do not assume'}).items()})
            cards = [{'game': g.model_dump(mode='json'), 'reasons': [], 'tradeoffs': []} for g in games] if index == 8 else []
            changed = (spec.get('initial_memory', {'platform': 'Linux', 'friend': 'Noor', 'plan_day': 'Saturday'}) if index == 0 else
                       spec.get('corrected_memory', {'plan_day': 'Sunday', 'budget': 'Unspecified; do not assume'}) if index == 40 else {})
            store.finish(turn, {'message': 'Noted for this synthetic long-history prefix.', 'games': cards,
                'notices': [], 'revision': index+1, 'total_turns': index+1,
                'memory_changes': [{'key': name, 'value': value, 'source_turn': rid} for name, value in changed.items()],
                'entities': [{'id': g.app_id, 'title': g.title} for g in games] if index == 8 else []}, memory,
                [{'synthetic_prefix': True, 'provider_calls': 0}])
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['development', 'held_out'], required=True)
    parser.add_argument('--max-new-turns', type=int, default=24, choices=range(1, 25))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', type=Path)
    parser.add_argument('--case-order', nargs='+')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    from game_discovery.core.settings import Settings
    settings = Settings.from_environment()
    configuration = {'model': settings.groq_model, 'daily_calls': settings.ai_daily_calls,
                     'daily_reserved_units': settings.ai_daily_tokens, 'max_model_calls_per_turn': 3,
                     'max_tool_calls_per_turn': 6, 'provider_input_bytes': 12000}
    cases_path = (args.cases or (root / 'data/evaluation/dialogue-v1.json')).resolve()
    cases = json.loads(cases_path.read_text(encoding='utf-8'))[args.split]
    if args.case_order:
        if len(args.case_order) != len(cases) or set(args.case_order) != {case['id'] for case in cases}:
            parser.error('--case-order must contain every case exactly once')
        by_id = {case['id']: case for case in cases}
        cases = [by_id[case_id] for case_id in args.case_order]
    configuration['case_order'] = [case['id'] for case in cases]
    private_path = Path('C:/Users/User/AppData/Local/Temp/opencode') / (args.output.stem + '.private.json')
    assert private_path.parent.is_dir() and args.output.parent.is_dir()
    current = identity(root, cases_path)
    journal = json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else {
        'version': 'llm-first-v1', 'split': args.split, 'source_identity': current,
        'runtime_configuration': configuration, 'cases': [], 'human_scores': None}
    if journal['source_identity'] != current:
        raise SystemExit('Source changed: preserve this journal and start a versioned experiment, never replace its hashes.')
    if journal.get('runtime_configuration') != configuration:
        raise SystemExit('Runtime model/limits changed; preserve this journal and version the continuation.')
    private = json.loads(private_path.read_text(encoding='utf-8')) if private_path.exists() else {}
    save(args.output, journal)
    new_turns = 0
    for case in cases:
        entry = next((c for c in journal['cases'] if c['id'] == case['id']), None)
        if entry is None:
            entry = {'id': case['id'], 'turns': [], 'seed_turns': case.get('seed_turns', 0)}
            journal['cases'].append(entry)
        if entry.get('finished'):
            continue
        if new_turns >= args.max_new_turns:
            save(args.output, journal)
            return
        wait_for_window(journal)
        secret = private.setdefault(case['id'], {'conversation_id': str(uuid4()), 'token': secrets.token_urlsafe(32)})
        save(private_path, private)
        status, created = post('/api/v2/assistant/conversations', {'messages': [], 'key': secret})
        if status != 200:
            entry['creation_error'] = {'status': status, 'response': created}
            save(args.output, journal)
            print(json.dumps({'case': case['id'], 'creation_status': status}))
            return
        if case.get('seed_turns'):
            seed_long(secret, private, private_path, case.get('seed_context'))
            entry['seed_kind'] = '80 persisted synthetic turns, zero model calls; live follow-ups measured separately'
        for index, message in enumerate(case['turns']):
            if index < len(entry['turns']):
                if entry['turns'][index].get('status') != 200:
                    entry['dependent_turns_skipped'] = len(case['turns']) - index - 1
                    break
                continue
            if new_turns >= args.max_new_turns:
                save(args.output, journal)
                return
            if identity(root, cases_path) != current:
                raise SystemExit('Source changed during evaluation; no further calls.')
            # Provider/application minute ceilings are respected, never reset.
            wait_for_window(journal)
            try:
                receipt = quota_receipt(root, settings.ai_daily_calls, settings.ai_daily_tokens)
            except Exception:
                journal['paused'] = {'reason': 'quota_receipt_unavailable', 'at': datetime.now(UTC).isoformat()}
                save(args.output, journal)
                return
            if receipt['remaining_calls'] < 3 or receipt['remaining_units'] < 39840:
                journal['paused'] = {'reason': 'insufficient_worst_case_turn_headroom', 'receipt': receipt}
                save(args.output, journal)
                print(json.dumps(journal['paused']))
                return
            if journal.get('paused'):
                journal.setdefault('pause_history', []).append(journal.pop('paused'))
            history_status, history = post('/api/v2/assistant/history', secret)
            if history_status != 200:
                entry['history_error'] = history
                save(args.output, journal)
                return
            turn = {'index': index, 'message': message, 'turn_id': str(uuid4()), 'status': 'started', 'at': datetime.now(UTC).isoformat()}
            entry['turns'].append(turn)
            journal['last_attempt_at'] = turn['at']
            turn['quota_before'] = receipt
            save(args.output, journal)
            save(Path('C:/Users/User/AppData/Local/Temp/opencode/llm-first-last-attempt.json'), {'at': turn['at']})
            started = time.perf_counter()
            status, response = post('/api/v2/assistant', {**secret, 'revision': history['revision'],
                'turn_id': turn['turn_id'], 'message': message})
            turn.update(status=status, response=response, elapsed_ms=round((time.perf_counter()-started)*1000, 3))
            _, archive = post('/api/v2/assistant/history', {**secret, 'before': 2147483647, 'limit': 10})
            turn['stored_event'] = next((e for e in archive.get('events', []) if e['id'] == turn['turn_id']), None)
            new_turns += 1
            save(args.output, journal)
            print(json.dumps({'case': case['id'], 'turn': index+1, 'status': status,
                              'message': response.get('message'), 'elapsed_ms': turn['elapsed_ms']}, ensure_ascii=True), flush=True)
            if status != 200:
                entry['dependent_turns_skipped'] = len(case['turns']) - index - 1
                if status in {429, 500, 503, 504}:
                    entry['finished'] = True
                    entry['cleanup_status'] = post('/api/v2/assistant/forget', secret)[0]
                    journal['paused'] = {'reason': 'service_limit_or_infrastructure_failure',
                        'case': case['id'], 'status': status, 'code': response.get('code'),
                        'retry_at': response.get('retry_at')}
                    save(args.output, journal)
                    return
                break
        entry['finished'] = True
        # Synthetic archives are explicitly erased after their public evidence is captured.
        entry['cleanup_status'] = post('/api/v2/assistant/forget', secret)[0]
        save(args.output, journal)
    print(json.dumps({'status': 'completed', 'split': args.split, 'new_turns': new_turns}))


if __name__ == '__main__':
    main()
