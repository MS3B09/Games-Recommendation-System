"""Opt-in isolated SQL archive checks. No inference or production archive writes."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from game_discovery.jobs.verify_ai_budget import connection_url


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    schema = 'conversation_verify_' + uuid4().hex[:12]
    checks: list[str] = []
    report = {'checks': checks, 'inference_calls': 0, 'production_archive_writes': 0, 'cleanup': False}
    cid, rid = uuid4(), uuid4()
    secret = hashlib.sha256(uuid4().bytes).hexdigest()
    runtime_url = connection_url(root / 'backend/.env', 'DATABASE_URL')
    with psycopg.connect(connection_url(root / 'backend/.env'), connect_timeout=5,
                          prepare_threshold=None, autocommit=True) as admin:
        before = admin.execute('select row_to_json(w) from discovery.ai_usage_windows w').fetchone()
        def runtime(sql, params=()):
            with psycopg.connect(runtime_url, connect_timeout=5, prepare_threshold=None) as connection:
                return connection.execute(sql.replace('discovery.', f'"{schema}".'), params).fetchone()
        try:
            admin.execute(f'create schema "{schema}"')
            admin.execute(f'grant usage on schema "{schema}" to game_discovery_runtime')
            sql = (root / 'backend/migrations/0008_conversation_archive.sql').read_text(encoding='utf-8')
            admin.execute(sql.replace('discovery.', f'"{schema}".'))
            admin.execute((root / 'backend/migrations/0009_archive_bootstrap_capacity.sql').read_text(encoding='utf-8').replace('discovery.', f'"{schema}".'))
            assert runtime('select discovery.conversation_create(%s,%s)', (cid, secret))[0]
            checks.append('runtime can create only through execute-only capability function')
            assert runtime('select discovery.conversation_read(%s,%s)', (cid, '0' * 64))[0] is None
            checks.append('wrong capability cannot read a conversation')
            initial = runtime('select discovery.conversation_read(%s,%s)', (cid, secret))[0]
            assert initial == {'revision': 0, 'document': {'events': [], 'memory': {}}}
            checks.append('new conversation is independent and empty')
            started = runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)', (cid, secret, rid, 0, 'Original input'))[0]
            assert started['document']['events'][0]['input'] == 'Original input'
            checks.append('user input is durable before provider work')
            assert runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)', (cid, secret, uuid4(), 0, 'Concurrent'))[0]['error'] == 'chat_busy'
            checks.append('committed lease prevents concurrent model work without holding a connection')
            assert runtime('select discovery.conversation_finish(%s,%s,%s,%s,%s,%s)',
                (cid, secret, rid, None, Jsonb({}), Jsonb([{'failure': 'simulated'}])))[0]
            failed = runtime('select discovery.conversation_read(%s,%s)', (cid, secret))[0]
            assert failed['revision'] == 0 and failed['document']['events'][0]['status'] == 'failed'
            checks.append('failure preserves original input and attempt without advancing accepted revision')
            retry = runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)', (cid, secret, rid, 0, 'Original input'))[0]
            assert len(retry['document']['events']) == 1
            response = {'message': 'A useful answer', 'games': [], 'revision': 1}
            memory = {'platform': {'value': 'Linux', 'source_turn': str(rid)}}
            assert runtime('select discovery.conversation_finish(%s,%s,%s,%s,%s,%s)',
                (cid, secret, rid, Jsonb(response), Jsonb(memory), Jsonb([{'tool': 'mock'}])))[0]
            saved = runtime('select discovery.conversation_read(%s,%s)', (cid, secret))[0]
            assert len(saved['document']['events'][0]['attempts']) == 2 and saved['document']['memory'] == memory
            checks.append('explicit retry appends attempt history; sourced working memory is durable')
            assert runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)', (cid, secret, rid, 0, 'Original input'))[0]['cached'] == response
            checks.append('completed turn re-delivery is idempotent and requires no inference')
            assert runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)', (cid, secret, rid, 1, 'Changed input'))[0]['error'] == 'chat_session_conflict'
            assert runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)', (cid, secret, uuid4(), 0, 'Stale'))[0]['error'] == 'chat_session_conflict'
            checks.append('turn reuse and stale revision cannot overwrite accepted conversation')
            other = uuid4()
            assert runtime('select discovery.conversation_create(%s,%s)', (other, secret))[0]
            assert runtime('select discovery.conversation_read(%s,%s)', (other, secret))[0]['document']['memory'] == {}
            checks.append('second chat shares neither preferences nor messages')
            try:
                runtime(f'select * from "{schema}".conversation_archives')
            except psycopg.errors.InsufficientPrivilege:
                checks.append('runtime cannot directly select private conversation tables')
            else:
                raise AssertionError('Direct table access')
            assert not runtime('select discovery.conversation_delete(%s,%s)', (cid, '0' * 64))[0]
            assert runtime('select discovery.conversation_delete(%s,%s)', (cid, secret))[0]
            assert runtime('select discovery.conversation_read(%s,%s)', (cid, secret))[0] is None
            checks.append('explicit erasure requires the matching capability and removes history')
            pending_id, replacement_id = uuid4(), uuid4()
            assert 'document' in runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)',
                (other, secret, pending_id, 0, 'Input before interrupted process'))[0]
            admin.execute(f'update "{schema}".conversation_archives set lease_until=clock_timestamp()-interval \'1 second\' where id=%s', (other,))
            recovered = runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)',
                (other, secret, replacement_id, 0, 'A new explicit turn'))[0]
            assert recovered['document']['events'][0]['status'] == 'interrupted'
            assert recovered['document']['events'][0]['input'] == 'Input before interrupted process'
            assert not runtime('select discovery.conversation_finish(%s,%s,%s,%s,%s,%s)',
                (other, secret, pending_id, Jsonb(response), Jsonb({}), Jsonb([])))[0]
            checks.append('expired lease preserves interrupted input; old completion cannot overwrite the new turn')
            assert runtime('select discovery.conversation_delete(%s,%s)', (other, secret))[0]
            assert not runtime('select discovery.conversation_finish(%s,%s,%s,%s,%s,%s)',
                (other, secret, replacement_id, Jsonb(response), Jsonb({}), Jsonb([])))[0]
            checks.append('erasing an in-flight chat prevents a late response from resurrecting it')
            imported = [{'id': str(uuid4()), 'input': 'Retained browser message', 'status': 'imported',
                         'output': {'message': 'Retained reply', 'card_payload': 'x' * 300000}}]
            imported_id = uuid4()
            assert runtime('select discovery.conversation_create(%s,%s,%s)', (imported_id, secret, Jsonb(imported)))[0]
            assert runtime('select discovery.conversation_read(%s,%s)', (imported_id, secret))[0]['document']['events'] == imported
            checks.append('larger canonical-card imports remain complete rather than failing the old 256KiB limit')
            assert not runtime('select discovery.conversation_create(%s,%s,%s)', (uuid4(), secret, Jsonb(imported * 21)))[0]
            checks.append('oversized or overlong bootstrap arrays fail explicitly without partial imports')
            admin.execute(f"update \"{schema}\".conversation_archives set document=jsonb_set(document,'{{memory}}',jsonb_build_object('padding',repeat('x',3650000))) where id=%s", (imported_id,))
            assert runtime('select discovery.conversation_begin(%s,%s,%s,%s,%s)',
                (imported_id, secret, uuid4(), 1, 'One more turn'))[0]['error'] == 'chat_archive_full'
            assert admin.execute(f'select document->\'events\' from "{schema}".conversation_archives where id=%s', (imported_id,)).fetchone()[0] == imported
            checks.append('per-chat capacity rejects a new turn without evicting original history')
            admin.execute(f"insert into \"{schema}\".conversation_archives(id,secret_hash,document) select gen_random_uuid(),%s,jsonb_build_object('events','[]'::jsonb,'memory',jsonb_build_object('padding',repeat('x',3932161))) from generate_series(1,8)", (secret,))
            assert not runtime('select discovery.conversation_create(%s,%s)', (uuid4(), secret))[0]
            checks.append('shared archive capacity is explicit and never silently deletes another chat')
            assert admin.execute('select row_to_json(w) from discovery.ai_usage_windows w').fetchone() == before
            checks.append('application accounting is untouched')
            report['status'] = 'passed'
        finally:
            admin.execute(f'drop schema if exists "{schema}" cascade')
            report['cleanup'] = admin.execute('select to_regnamespace(%s) is null', (schema,)).fetchone()[0]
            report['at'] = datetime.now(UTC).isoformat()
            (root / 'docs/reports/llm-first-archive-scratch.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
