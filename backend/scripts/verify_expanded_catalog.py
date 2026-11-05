"""Opt-in staged-catalog acceptance with real restricted reads in an owned private schema.

Copies both catalog generations, never chat/usage data. Public activation is untouched.
Interactive serving uses the real shared archive and metered AI when configured.
"""

import argparse
import json
import math
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import psutil
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from game_discovery.catalog.contracts import Filters, Game, digest
from game_discovery.catalog.discovery import satisfies
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.database_url import normalize_db_url
from game_discovery.jobs.catalog import load_games, write_json

TABLES = {
    'catalog_versions': 'version,created_at,activated_at,active,game_count,model_id,model_revision,dimensions,region,currency,source_observed_at,artifact_manifest,analytics_manifest',
    'games': 'version,app_id,title,normalized_title,description,eligibility,semantic_hash,document,identity_title,compact_title,title_tokens',
    'game_platforms': 'version,app_id,platform,supported',
    'game_terms': 'version,app_id,kind,term',
    'game_prices': 'version,app_id,amount_cents,free_to_play,region,currency,observed_at',
    'game_embeddings': 'version,app_id,semantic_hash,embedding',
    'game_dashboard_metadata': 'version,app_id,document',
    'catalog_analytics': 'version,sha256,document',
}
OWNER_TAG = 'game-discovery-owned-expanded-acceptance-v1'


def timings(samples):
    ordered = sorted(samples)
    assert ordered
    return {'samples': len(ordered), 'p50_ms': round(ordered[(len(ordered) - 1) // 2], 3),
            'p95_ms': round(ordered[math.ceil(len(ordered) * .95) - 1], 3),
            'max_ms': round(ordered[-1], 3)}


def verify(run, env_file, output, serve_port=None):
    if serve_port is not None:
        import socket
        with socket.socket() as port_check:
            port_check.bind(('127.0.0.1', serve_port))
    # The imported module's global app must not load a second model or any live AI client.
    os.environ.update(GAME_DISCOVERY_ENV_FILE='C:/Users/User/AppData/Local/Temp/opencode/catalog-unit-no-env',
                      AI_ENABLED='false', QUERY_TOKENIZER_PATH='', QUERY_MODEL_PATH='', QUERY_ARTIFACT_PATH='')
    from fastapi.testclient import TestClient
    from game_discovery.api.main import create_app
    from game_discovery.ai.dialogue import Dialogue
    from game_discovery.core.settings import Settings
    from game_discovery.db.readiness import CatalogReadiness
    from game_discovery.retrieval.chat import ChatRetriever
    from game_discovery.retrieval.query import load_query_encoder

    config = dotenv_values(env_file, interpolate=False)
    games, _ = load_games(run)
    artifact = json.loads((run / 'artifact.json').read_text(encoding='utf-8'))
    required = json.loads((run / 'required-ids.json').read_text(encoding='utf-8'))
    assert len(games) == len({g.app_id for g in games}) == 2000 and len(required) == 40
    version = artifact['version']

    def engine(key):
        return create_engine(make_url(normalize_db_url(config[key])).set(drivername='postgresql+psycopg'),
                             hide_parameters=True, pool_size=2, max_overflow=0, pool_timeout=1,
                             connect_args={'prepare_threshold': None, 'connect_timeout': 10})

    admin, runtime = engine('MIGRATION_DATABASE_URL'), engine('DATABASE_URL')
    schema = 'catalog_preview_' + uuid.uuid4().hex[:12]
    report = {'status': 'in_progress', 'version': version, 'games': len(games), 'private_schema': schema,
              'scope': 'Actual staged documents/vectors; restricted PostgreSQL reads; in-process ASGI, not hosted HTTP or LLM quality.',
              'checks': [], 'api_samples': [], 'chat_samples': []}
    created = False
    try:
        with admin.begin() as c:
            c.execute(text("SET LOCAL statement_timeout='120s'"))
            old = c.execute(text('select version from discovery.catalog_versions where active')).scalar_one()
            assert old != version
            assert c.execute(text('select game_count from discovery.catalog_versions where version=:v and not active'), {'v': version}).scalar_one() == 2000
            before = [row[0] for row in c.execute(text('select document from discovery.games where version=:v order by app_id'), {'v': old})]
            assert len(before) == 40
            c.execute(text(f'create schema {schema}'))
            created = True
            c.execute(text(f"comment on schema {schema} is '{OWNER_TAG}'"))
            c.execute(text(f'revoke all on schema {schema} from public'))
            for table, columns in TABLES.items():
                c.execute(text(f'create table {schema}.{table} (like discovery.{table} including all)'))
                c.execute(text(f'insert into {schema}.{table}({columns}) select {columns} from discovery.{table} where version=any(:versions)'),
                          {'versions': [old, version]})
            c.execute(text(f'alter table {schema}.games add foreign key(version) references {schema}.catalog_versions(version)'))
            for table in tuple(TABLES)[2:]:
                if table == 'catalog_analytics':
                    c.execute(text(f'alter table {schema}.{table} add foreign key(version) references {schema}.catalog_versions(version)'))
                    continue
                c.execute(text(f'alter table {schema}.{table} add foreign key(version,app_id) references {schema}.games(version,app_id)'))
            c.execute(text(f'update {schema}.catalog_versions set active=false where active'))
            c.execute(text(f'update {schema}.catalog_versions set active=true,activated_at=now() where version=:v'), {'v': version})
            c.execute(text(f'grant usage on schema {schema} to game_discovery_runtime'))
            for table in TABLES:
                c.execute(text(f'alter table {schema}.{table} enable row level security'))
                c.execute(text(f'revoke all on {schema}.{table} from public,anon,authenticated'))
                c.execute(text(f'grant select on {schema}.{table} to game_discovery_runtime'))
                predicate = 'active' if table == 'catalog_versions' else f'exists(select 1 from {schema}.catalog_versions v where v.version={table}.version and v.active)'
                c.execute(text(f'create policy active_read on {schema}.{table} for select to game_discovery_runtime using({predicate})'))
                c.execute(text(f'analyze {schema}.{table}'))
            report['private_relations_bytes'] = {table: c.execute(text('select pg_total_relation_size(cast(:name as regclass))'),
                                                                 {'name': f'{schema}.{table}'}).scalar_one() for table in TABLES}

        class ScopedConnection:
            def __init__(self, connection):
                self.connection = connection

            def execute(self, statement, params=None):
                return self.connection.execute(text(str(statement).replace('discovery.', schema + '.')), params or {})

        class ScopedRepository(CatalogRepository):
            @contextmanager
            def snapshot(self):
                with runtime.connect().execution_options(isolation_level='REPEATABLE READ', postgresql_readonly=True) as c, c.begin():
                    scoped = ScopedConnection(c)
                    elevated, active, _ = scoped.execute(text("""select rolsuper or rolcreatedb or rolcreaterole or rolbypassrls,
                        (select version from discovery.catalog_versions where active),set_config('statement_timeout','2s',true)
                        from pg_roles where rolname=current_user""")).one()
                    assert not elevated and active is not None
                    yield scoped, active

        repo = ScopedRepository(runtime)

        def probe():
            with repo.snapshot() as (c, active):
                row = c.execute(text('select game_count,source_observed_at from discovery.catalog_versions where version=:v'), {'v': active}).one()
                return CatalogReadiness(version=active, game_count=row[0], observed_at=row[1])

        with repo.snapshot() as (c, active):
            assert active == version
            assert c.execute(text('select count(*) from discovery.game_dashboard_metadata')).scalar_one() == 2000
            assert c.execute(text('select count(*) from discovery.games where version=:v'), {'v': old}).scalar_one() == 0
            assert c.execute(text('select has_table_privilege(current_user,:name,\'INSERT\')'), {'name': f'{schema}.games'}).scalar_one() is False
        report['checks'].append('restricted active-only catalog/metadata reads, inactive hidden, writes denied')
        beyond = next(g for g in games[256:] if len(g.title) <= 180)
        assert repo.chat_title(beyond.title).match.kind == 'found'
        assert repo.chat_title('', beyond.app_id).games[0].app_id == beyond.app_id
        assert repo.chat_title('Portal-2').games[0].app_id == 620
        assert repo.chat_title('ori').match.kind == 'ambiguous'
        assert repo.chat_title('zzzz-no-such-catalog-title-zzzz').match.kind == 'not_in_catalog'
        report['beyond_256_identity'] = {'app_id': beyond.app_id, 'title': beyond.title}
        report['checks'].append('complete title/reference matching beyond 256, punctuation, ambiguity and absence')

        encoder = load_query_encoder(config['QUERY_TOKENIZER_PATH'], config['QUERY_MODEL_PATH'], str(run / 'artifact.json'))
        assert encoder is not None and encoder.catalog_version == version
        settings = Settings(allowed_origins=('http://127.0.0.1:4173', 'http://localhost:4173')) if serve_port else Settings()
        assistant = archive = None
        if serve_port:
            from game_discovery.ai.conversation_store import ConversationStore
            from game_discovery.ai.provider import DatabaseBudget, GroqAssistant
            settings = Settings.model_validate({key.lower(): value for key, value in config.items()
                if key.lower() in Settings.model_fields and value is not None and key != 'ALLOWED_ORIGINS'} | {
                'allowed_origins': settings.allowed_origins, 'ai_daily_calls': 50, 'ai_daily_tokens': 500000})
            archive = ConversationStore(runtime)
            if settings.ai_enabled and settings.groq_api_key.get_secret_value():
                assistant = GroqAssistant(settings, DatabaseBudget(runtime, settings.ai_daily_calls, settings.ai_daily_tokens))
        # Acceptance requests must never invoke live AI; attach it only for interactive serving below.
        app = create_app(settings, catalog_probe=probe, repository=repo, query_encoder=encoder)
        canonical = {g.app_id: g.model_dump(mode='json') for g in games}
        with TestClient(app) as client:
            def request(method, route, body=None):
                started = time.perf_counter()
                response = client.request(method, route, json=body) if body is not None else client.get(route)
                report['api_samples'].append({'route': route, 'status': response.status_code,
                                              'elapsed_ms': round((time.perf_counter() - started) * 1000, 3)})
                assert response.status_code == 200, (route, response.status_code)
                return response.json()

            assert request('GET', '/health/ready')['catalog_version'] == version
            status = request('GET', '/api/v1/catalog/status')
            assert status['game_count'] == 2000 and status['semantic_query_matching'] and not status['llm_enabled']
            first = request('GET', '/api/v1/games?limit=50')
            last = request('GET', '/api/v1/games?limit=50&offset=1950')
            assert first['total'] == last['total'] == 2000 and len(last['items']) == 50
            assert not {g['app_id'] for g in first['items']} & {g['app_id'] for g in last['items']}
            saved = request('POST', '/api/v1/games/resolve', {'app_ids': required + [2147483647]})
            assert len(saved['items']) == 40 and saved['unknown_ids'] == [2147483647]
            saved_ids = sorted(required + [g.app_id for g in games if g.app_id not in required][:160])
            saved = request('POST', '/api/v1/games/resolve', {'app_ids': saved_ids})
            assert len(saved['items']) == 200 and not saved['unknown_ids']
            assert {g['app_id'] for g in saved['items']} == set(saved_ids)
            assert request('GET', '/api/v1/games/' + str(beyond.app_id)) == canonical[beyond.app_id]
            assert request('GET', '/api/v1/facets')['max_price_cents'] == max(g.price.amount_cents for g in games if g.price)
            assert request('GET', '/api/v1/analytics')['data']['total_games'] == 2000
            cases = [Filters(), Filters(platforms=['windows'], required_modes=['single-player'], max_price_cents=2000),
                     Filters(free_only=True), Filters(platforms=['mac', 'linux'], platform_match='all'),
                     Filters(required_modes=['online-co-op']), Filters(required_modes=['local-co-op']),
                     Filters(required_genres=['action', 'rpg']), Filters(min_price_cents=1000, max_price_cents=2000),
                     Filters(max_price_cents=0, price_operator='lt'), Filters(excluded_ids=[g['app_id'] for g in first['items']])]
            for filters in cases:
                body = request('POST', '/api/v1/discover', {'favorite_ids': [1145360], 'filters': filters.model_dump(), 'limit': 20})
                assert body['catalog_version'] == version and body['effective_criteria'] == filters.model_dump()
                for item in body['results']:
                    game = Game.model_validate(item['game'])
                    assert item['game'] == canonical[game.app_id] and satisfies(game, filters, {1145360, *filters.excluded_ids})
                    assert all(set(reason['evidence_ids']) <= {e.id for e in game.evidence} for reason in item['reasons'])
                if filters.max_price_cents == 0 and filters.price_operator == 'lt':
                    assert not body['results'] and body['suggested_refinements']
            semantic = request('POST', '/api/v1/discover', {'query': 'cooperative puzzle', 'filters': {'platforms': ['windows']}, 'limit': 20})
            assert semantic['capabilities']['semantic_query_matching'] and semantic['results']
            report['checks'].append('real API readiness, pagination, saved IDs, canonical cards, facets, ten hard-filter cases and actual semantic discovery')

        retriever = ChatRetriever(repo, encoder)
        for query in ('cooperative puzzle', 'story adventure', 'action combat progression'):
            for filters in cases[:4]:
                started = time.perf_counter()
                result = retriever.recommend(query, filters)
                assert result.outcome.kind != 'retrieval_unavailable' and result.outcome.semantic_available
                for candidate in result.candidates:
                    assert candidate.game.model_dump(mode='json') == canonical[candidate.game.app_id]
                    assert satisfies(candidate.game, filters, set(filters.excluded_ids))
                report['chat_samples'].append({'query': query, 'filters': filters.model_dump(exclude_defaults=True),
                                              'elapsed_ms': round((time.perf_counter() - started) * 1000, 3),
                                              'returned': len(result.candidates)})
        # Catalog tools are exercised directly, with no model or archive access.
        dialogue = Dialogue(None, repo, None, encoder)
        page = dialogue.tool('lookup_titles', {'query': '', 'limit': 30, 'offset': 1970}, {}, 'catalog-check')
        assert page['total_matches'] == 2000 and page['returned'] == 30 and page['next_offset'] is None
        facts = dialogue.tool('game_details', {'ids': [beyond.app_id], 'fields': ['developers', 'title']}, {}, 'details-check')
        assert 'developers' in facts['games'][0]['unavailable_direct_fields']
        assert 'developers' not in facts['games'][0]['available_fields']
        native_filters = Filters(platforms=['windows'], required_modes=['online-co-op'])
        packet = dialogue.tool('recommend_games', {'query': 'cooperative puzzle', 'filters': native_filters.model_dump(),
                              'save_as_normal': False, 'limit': 4, 'excluded_titles': ['Portal 2']}, {}, 'recommend-check')
        assert packet['games'] and packet['outcome']['semantic_available']
        for item in packet['games']:
            assert satisfies(dialogue.games[item['id']], native_filters, {620})
            assert all(fact['field'] not in {'developers', 'reviews', 'release_date'} for fact in item['facts'])
        report['checks'].append('real chat 20+20 RRF retrieval with twelve filtered samples; native paging/details/recommendations preserve legacy evidence isolation')

        with admin.connect() as c:
            c.execute(text(f'update {schema}.catalog_versions set active=false where active'))
            c.execute(text(f'update {schema}.catalog_versions set active=true,activated_at=now() where version=:v'), {'v': old})
            assert repo.search('', 1, 0).total == 2000  # Uncommitted rollback is invisible to readers.
            c.rollback()
            assert repo.search('', 1, 0).total == 2000
            for target, expected in ((old, 40), (version, 2000)):
                with c.begin():
                    c.execute(text(f'update {schema}.catalog_versions set active=false where active'))
                    c.execute(text(f'update {schema}.catalog_versions set active=true,activated_at=now() where version=:v'), {'v': target})
                assert repo.search('', 1, 0).total == expected
        report['checks'].append('isolated atomic switch/rollback: uncommitted change invisible; committed 2000→40→2000 roundtrip')
        report['api_timings'] = timings([s['elapsed_ms'] for s in report['api_samples']])
        report['chat_retrieval_timings'] = timings([s['elapsed_ms'] for s in report['chat_samples']])
        report['api_probe_peak_working_set_bytes'] = psutil.Process().memory_info().peak_wset
        if serve_port is not None:
            import uvicorn
            app = create_app(settings, catalog_probe=probe, repository=repo, query_encoder=encoder,
                             assistant=assistant, conversation_store=archive)
            write_json(output.with_name(output.stem + '-preview.json'), {'state': 'serving_isolated_preview',
                       'port': serve_port, 'schema': schema, 'owner_tag': OWNER_TAG, 'catalog_version': version,
                       'llm_enabled': assistant is not None, 'archive_enabled': True,
                       'ai_daily_calls': settings.ai_daily_calls, 'ai_daily_tokens': settings.ai_daily_tokens,
                       'note': 'Expanded catalog for all preview services; real shared archive and metered AI. Public activation unchanged. Graceful exit removes exact private catalog schema.'})
            uvicorn.run(app, host='127.0.0.1', port=serve_port, log_level='warning')
    finally:
        runtime.dispose()
        with admin.begin() as c:
            if created:
                owned = c.execute(text("select pg_get_userbyid(nspowner)=current_user,obj_description(oid,'pg_namespace') from pg_namespace where nspname=:s"), {'s': schema}).one_or_none()
                if owned is not None:
                    assert tuple(owned) == (True, OWNER_TAG), 'Refusing cleanup without exact scratch ownership'
                    c.execute(text(f'drop schema {schema} cascade'))
            assert not c.execute(text('select exists(select 1 from pg_namespace where nspname=:s)'), {'s': schema}).scalar_one()
            report['private_schema_removed'] = True
            if 'before' in locals():
                assert c.execute(text('select version from discovery.catalog_versions where active')).scalar_one() == old
                after = [row[0] for row in c.execute(text('select document from discovery.games where version=:v order by app_id'), {'v': old})]
                assert before == after
                report['public_active_version_unchanged'] = old
                report['public_active_documents_sha256'] = digest(after)
            report['database_bytes_after_cleanup'] = c.execute(text('select pg_database_size(current_database())')).scalar_one()
        admin.dispose()
    report.update(status='passed', actual_llm_calls=None if serve_port else 0,
                  actual_reservations=None if serve_port else 0, public_activation=False)
    if serve_port:
        report['interactive_usage'] = 'Interactive AI uses the unchanged shared accounting ledger; not included in acceptance timings.'
    write_json(output, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--serve-port', type=int, choices=[8002], help='Serve all local app services using the expanded catalog, real shared archive and configured metered AI until graceful exit')
    args = parser.parse_args()
    try:
        result = verify(args.run_dir, args.env_file, args.output, args.serve_port)
        print(json.dumps({key: value for key, value in result.items() if key not in ('api_samples', 'chat_samples')}, indent=2))
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__,
                          'assertion': str(error) if isinstance(error, AssertionError) else None}))
        raise SystemExit(1)
