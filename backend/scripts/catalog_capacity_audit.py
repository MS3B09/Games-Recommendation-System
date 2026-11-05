"""Task 1A only: local pilot and rollback-only sizing; never publish a catalog."""

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

import psutil
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from game_discovery.catalog.contracts import Embedding, Source, digest, semantic_text
from game_discovery.core.database_url import db_url_matches_project, normalize_db_url
from game_discovery.jobs.audit import steam_app_id
from game_discovery.jobs.catalog import load_games, normalize, normalize_payload, validated_artifact, write_json
from game_discovery.jobs.probe import verified_review_summary

ROOT = Path(__file__).resolve().parents[2]
TABLES = ('games', 'game_platforms', 'game_terms', 'game_prices', 'game_embeddings')


def engine_for(config, key, project):
    value = config.get(key)
    if not db_url_matches_project(value, project):
        raise ValueError('Missing or mismatched database project')
    return create_engine(make_url(normalize_db_url(value)).set(drivername='postgresql+psycopg'),
                         hide_parameters=True, connect_args={'prepare_threshold': None, 'connect_timeout': 10})


def snapshot(config, project, output):
    engine = engine_for(config, 'DATABASE_URL', project)
    try:
        with engine.connect().execution_options(postgresql_readonly=True) as connection, connection.begin():
            connection.execute(text("SET LOCAL statement_timeout='5s'"))
            elevated = connection.execute(text('select rolsuper or rolcreatedb or rolcreaterole or rolbypassrls from pg_roles where rolname=current_user')).scalar_one()
            if elevated:
                raise ValueError('Runtime role must be restricted')
            versions = [dict(row) for row in connection.execute(text('select * from discovery.catalog_versions order by version')).mappings()]
            games = [row[0] for row in connection.execute(text('select document from discovery.games order by app_id'))]
            sizes = [dict(row) for row in connection.execute(text("""select n.nspname as schema,c.relname as name,
                pg_table_size(c.oid) as table_bytes,pg_indexes_size(c.oid) as index_bytes,
                pg_total_relation_size(c.oid) as total_bytes from pg_class c join pg_namespace n on n.oid=c.relnamespace
                where c.relkind='r' and n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%'
                order by n.nspname,c.relname"""
            )).mappings()]
            database_bytes = connection.execute(text('select pg_database_size(current_database())')).scalar_one()
        write_json(output / 'active-games.json', games)
        report = {'observed_at': datetime.now(UTC).isoformat(), 'restricted_role': True,
                  'versions_visible_to_runtime': versions, 'active_games': len(games),
                  'database_bytes': database_bytes, 'relations': sizes,
                  'memory': psutil.virtual_memory()._asdict(),
                  'disk': {drive: psutil.disk_usage(drive)._asdict() for drive in ('C:/', 'E:/')}}
    finally:
        engine.dispose()
    # Aggregate-only privileged read: no archive documents, IDs, capabilities or messages.
    engine = engine_for(config, 'MIGRATION_DATABASE_URL', project)
    try:
        with engine.connect().execution_options(postgresql_readonly=True) as connection, connection.begin():
            connection.execute(text("SET LOCAL statement_timeout='5s'"))
            report['all_versions'] = [dict(row) for row in connection.execute(text('select version,active,game_count,source_observed_at from discovery.catalog_versions order by version')).mappings()]
            report['archive'] = dict(connection.execute(text("""select count(*) as archives,
                coalesce(sum(octet_length(document::text)),0) as document_bytes,
                coalesce(max(octet_length(document::text)),0) as largest_document_bytes,
                count(*) filter(where pending is not null) as pending from discovery.conversation_archives"""
            )).mappings().one())
            report['migration'] = connection.execute(text('select version_num from discovery_migrations.alembic_version')).scalar_one()
    finally:
        engine.dispose()
    write_json(output / 'snapshot.json', json.loads(json.dumps(report, default=str)))
    return {'games': len(games), 'database_bytes': database_bytes, 'archive': report['archive']}


def candidates(output, pilot):
    active = json.loads((output / 'active-games.json').read_text(encoding='utf-8'))
    by_id = {g['app_id']: {'app_id': g['app_id'], 'title': g['title'], 'origins': ['active_catalog'],
                          'reason': 'retain existing eligible identity',
                          'coverage': {'genres': g['genres'], 'modes': g['modes'], 'platforms': g['platforms']}}
             for g in active}
    inputs = []
    for filename in ('game_data_for_dashboard.csv', 'games_data_recomendation.csv'):
        path = ROOT / filename
        with path.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        inputs.append({'file': filename, 'sha256': sha})
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                app_id = steam_app_id(row.get('Link', ''))
                if not app_id:
                    continue
                item = by_id.setdefault(app_id, {'app_id': app_id, 'title': row['title'], 'origins': [],
                    'reason': 'legacy candidate only; eligibility, popularity and all facts require fresh validation',
                    'coverage': {'legacy_genre_raw': row.get('genre'), 'legacy_tags_raw': row.get('tags')}})
                if filename not in item['origins']:
                    item['origins'].append(filename)
    for lead in pilot:
        item = by_id.setdefault(lead['app_id'], {**lead, 'origins': [], 'coverage': {}})
        item['pilot_reason'] = lead['reason']
        item['origins'].append('fixed_capacity_pilot')
    result = {'schema_version': 1, 'input_files': inputs, 'eligible_target': None,
              'note': 'Candidate leads, NOT a validated catalog or popularity ranking.',
              'candidates': [by_id[i] for i in sorted(by_id)]}
    write_json(output / 'candidates.json', result)
    return {'unique_candidates': len(by_id), 'active_retained': len(active), 'pilot': len(pilot),
            'pilot_legacy_overlap': sum(any('csv' in s for s in by_id[g['app_id']]['origins']) for g in pilot)}


def fetch(url, path):
    started = time.perf_counter()
    with urlopen(Request(url, headers={'User-Agent': 'GameDiscoveryCapacityAudit/0.1'}), timeout=20) as response:
        body = response.read(2 * 1024**2 + 1)
        if response.status != 200 or len(body) > 2 * 1024**2:
            raise ValueError('Invalid bounded source response')
    path.write_bytes(body)
    payload = json.loads(body)
    return payload, {'url': url, 'collected_at': datetime.now(UTC).isoformat(),
                     'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body),
                     'elapsed_seconds': time.perf_counter() - started}


def collect(output, pilot):
    run = output / 'pilot'
    run.mkdir(parents=True, exist_ok=True)
    path = run / 'collection.json'
    ids = [g['app_id'] for g in pilot]
    if not 1 <= len(ids) <= 100 or len(set(ids)) != len(ids):
        raise ValueError('Pilot must contain 1–100 distinct IDs')
    report = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'schema_version': 1, 'region': 'US', 'app_ids': ids, 'observations': []}
    if report['app_ids'] != ids:
        raise ValueError('Immutable pilot identity mismatch')
    # Audit resumption never retries an attempted request, including failures.
    complete = {g['app_id'] for g in report['observations']}
    for app_id in ids:
        if app_id in complete:
            continue
        item = {'app_id': app_id}
        try:
            payload, source = fetch(f'https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=english', run / f'{app_id}-appdetails.json')
            normalized_source = {k: source[k] for k in ('url', 'collected_at', 'sha256')}
            normalize_payload(app_id, payload, Source.model_validate(normalized_source))
            item.update(source=normalized_source, snapshot=f'{app_id}-appdetails.json', transport=source)
        except Exception as error:
            item['error_type'] = type(error).__name__
            item['http_status'] = error.code if isinstance(error, HTTPError) else None
        report['observations'].append(item)
        write_json(path, report)
        print(json.dumps({'app_id': app_id, 'collected': 'source' in item, 'error': item.get('error_type')}), flush=True)
        if item.get('error_type'):
            return {'status': 'stopped_on_source_failure', 'app_id': app_id}
        time.sleep(2)
    return normalize(run)


def review_probe(output):
    run = output / 'pilot'
    report = json.loads((run / 'collection.json').read_text(encoding='utf-8'))
    reviews_path = run / 'reviews-v2.json'
    reviews = json.loads(reviews_path.read_text(encoding='utf-8')) if reviews_path.exists() else []
    for item in report['observations']:
        app_id = item['app_id']
        if app_id in {r['app_id'] for r in reviews} or not item.get('source'):
            continue
        result = {'app_id': app_id}
        try:
            filters = {'appid': app_id, 'filter': 0, 'languages': ['all'], 'purchase_type': 1,
                       'review_type': 0, 'num_per_page': 1, 'day_range': 0,
                       'filter_offtopic_activity': True, 'display_language': 'english'}
            url = 'https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/?' + urlencode({'input_json': json.dumps(filters)})
            payload, source = fetch(url, run / f'{app_id}-reviews-v2.json')
            response = payload.get('response', payload)
            summary = verified_review_summary({'success': 1, 'query_summary': response.get('query_summary')}, True)
            if summary is None:
                raise ValueError('Invalid review counts')
            result.update(summary=summary, source=source, scope=filters,
                          individual_reviews_returned=len(response.get('reviews', [])))
        except Exception as error:
            result.update(error_type=type(error).__name__, http_status=error.code if isinstance(error, HTTPError) else None)
        reviews.append(result)
        write_json(reviews_path, reviews)
        if result.get('error_type'):
            return {'status': 'stopped_on_review_failure', 'app_id': app_id}
        time.sleep(2)
    return {'review_requests': len(reviews), 'verified_summaries': sum('summary' in r for r in reviews)}


def percentile(values):
    ordered = sorted(values)
    return {'samples': len(values), 'p50_ms': round(ordered[(len(values) - 1) // 2], 3),
            'p95_ms': round(ordered[math.ceil(len(values) * .95) - 1], 3)}


def api_memory(config, output):
    # Configure only this disposable process before importing the one global app.
    os.environ.update(AI_ENABLED='false', DATABASE_URL=config['DATABASE_URL'],
                      **{key: config[key] for key in
                         ('QUERY_TOKENIZER_PATH', 'QUERY_MODEL_PATH', 'QUERY_ARTIFACT_PATH')})
    from fastapi.testclient import TestClient
    from game_discovery.api.main import app
    started = time.perf_counter()
    samples = []
    active_count = None
    with TestClient(app) as client:
        for method, route, body in (
            ('GET', '/health/ready', None), ('GET', '/api/v1/games?limit=50', None),
            ('GET', '/api/v1/facets', None),
            ('POST', '/api/v1/discover', {'favorite_ids': [1145360], 'limit': 20}),
            ('POST', '/api/v1/discover', {'query': 'cooperative puzzle', 'filters': {'platforms': ['windows'], 'max_price_cents': 2000}, 'limit': 20}),
        ):
            start = time.perf_counter()
            response = client.request(method, route, json=body) if body is not None else client.get(route)
            samples.append({'route': route, 'status': response.status_code,
                            'elapsed_ms': (time.perf_counter() - start) * 1000, 'response_bytes': len(response.content)})
            if response.status_code != 200:
                raise ValueError('Read-only API memory probe failed')
            if route == '/api/v1/games?limit=50':
                active_count = response.json()['total']
    report = {'observed_at': datetime.now(UTC).isoformat(), 'active_games': active_count, 'ai_enabled': False,
              'transport': 'in-process ASGI TestClient, not network HTTP or hosted runtime',
              'samples': samples, 'elapsed_seconds': time.perf_counter() - started,
              'peak_working_set_bytes': psutil.Process().memory_info().peak_wset}
    write_json(output / 'api-memory.json', report)
    return report


def measure(config, project, output):
    from game_discovery.retrieval.encoder import OnnxEncoder

    run = output / 'pilot'
    games, _ = load_games(run)
    manifest = json.loads(Path(config['QUERY_ARTIFACT_PATH']).read_text(encoding='utf-8'))
    for key, expected in (('QUERY_MODEL_PATH', 'model_sha256'), ('QUERY_TOKENIZER_PATH', 'tokenizer_sha256')):
        with Path(config[key]).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != manifest[expected]:
                raise ValueError('Pinned model bytes mismatch')
    started = time.perf_counter()
    encoder = OnnxEncoder(Path(config['QUERY_TOKENIZER_PATH']), Path(config['QUERY_MODEL_PATH']))
    load_seconds = time.perf_counter() - started
    vectors = []
    started = time.perf_counter()
    for offset in range(0, len(games), 8):
        batch = games[offset:offset + 8]
        encoded = encoder.encode([semantic_text(g) for g in batch])
        vectors.extend(Embedding(app_id=g.app_id, semantic_hash=g.semantic_hash, vector=v.tolist()).model_dump()
                       for g, v in zip(batch, encoded, strict=True))
        write_json(run / 'embeddings.json', vectors)
    embedding_seconds = time.perf_counter() - started
    write_json(run / 'embedding-settings.json', {k: manifest[k] for k in ('model_id', 'model_revision', 'model_sha256', 'tokenizer_sha256')})
    normalized = json.loads((run / 'normalized.json').read_text(encoding='utf-8'))
    artifact = {**normalized, 'embeddings_sha256': digest(vectors),
                'encoder': 'float-onnx-cpu-parity-verified',
                **{k: manifest[k] for k in ('model_sha256', 'tokenizer_sha256')}}
    artifact['version'] = 'm2-' + digest(artifact)[:24]
    write_json(run / 'artifact.json', artifact)
    validated_artifact(run)
    reviews = {r['app_id']: r for r in json.loads((run / 'reviews-v2.json').read_text(encoding='utf-8')) if r.get('summary')}
    documents = []
    for game in games:
        data = json.loads((run / f'{game.app_id}-appdetails.json').read_text(encoding='utf-8'))[str(game.app_id)]['data']
        source = game.evidence[0].source.model_dump(mode='json')
        dashboard = {'schema_version': 'capacity-proposal-v0', 'developers': data.get('developers'),
                     'release_date': data.get('release_date'), 'price_overview': data.get('price_overview'),
                     'steamos': None, 'source': source, 'reviews': reviews.get(game.app_id)}
        documents.append({**game.model_dump(mode='json'), 'dashboard': dashboard})
    write_json(run / 'proposed-documents.json', documents)
    terms = Counter(word.casefold() for g in games for word in g.description.split() if word.isalpha())
    # Storage envelope only, not Task 2's final analytics semantics/layout.
    aggregate = {'catalog_version': artifact['version'], 'total': len(games), 'word_frequencies': terms.most_common(250),
                 'dimensions': {k: dict(Counter(str(d['dashboard'].get(k)) for d in documents))
                                for k in ('developers', 'release_date', 'price_overview')}}
    write_json(run / 'aggregate-envelope.json', aggregate)
    report = {'observed_at': datetime.now(UTC).isoformat(), 'pilot_games': len(games),
              'encoder_load_seconds': load_seconds, 'embedding_seconds_including_checkpoint_writes': embedding_seconds,
              'model_revision': manifest['model_revision'], 'vector_dimensions': 384,
              'artifact_version': artifact['version'], 'model_hashes_verified': True,
              'file_bytes': {p.name: p.stat().st_size for p in run.glob('*.json') if p.name in
                             ('games.json', 'embeddings.json', 'proposed-documents.json', 'aggregate-envelope.json')},
              'peak_working_set_bytes': psutil.Process().memory_info().peak_wset,
              'coverage': {k: sum(d['dashboard'].get(k) is not None for d in documents)
                           for k in ('developers', 'release_date', 'price_overview', 'reviews', 'steamos')},
              'scales': []}
    # TEMP relations copy real generated columns/checks/indexes. No production rows, grants or activation touched.
    engine = engine_for(config, 'MIGRATION_DATABASE_URL', project)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text("SET LOCAL statement_timeout='120s'"))
                for name in TABLES:
                    connection.execute(text(f'CREATE TEMP TABLE capacity_{name} (LIKE discovery.{name} INCLUDING ALL) ON COMMIT DROP'))
                connection.execute(text('CREATE TEMP TABLE capacity_analytics(version text primary key, document jsonb not null) ON COMMIT DROP'))
                version = artifact['version']
                started = time.perf_counter()
                for game, document, vector in zip(games, documents, vectors, strict=True):
                    p = {'v': version, 'id': game.app_id}
                    connection.execute(text('insert into capacity_games(version,app_id,title,normalized_title,description,eligibility,semantic_hash,document) values(:v,:id,:title,:normalized,:description,:eligible,:hash,cast(:doc as jsonb))'),
                                       {**p, 'title': game.title, 'normalized': game.title.casefold(), 'description': game.description, 'eligible': game.eligibility, 'hash': game.semantic_hash, 'doc': json.dumps(document)})
                    for platform, supported in game.platforms.items():
                        connection.execute(text('insert into capacity_game_platforms values(:v,:id,:platform,:supported)'), {**p, 'platform': platform, 'supported': supported})
                    for kind, labels in (('genre', game.genres), ('tag', game.tags), ('mode', game.modes)):
                        for label in sorted(set(labels)):
                            connection.execute(text('insert into capacity_game_terms values(:v,:id,:kind,:term)'), {**p, 'kind': kind, 'term': label})
                    connection.execute(text("insert into capacity_game_prices values(:v,:id,:amount,:free,'US','USD',:observed)"),
                                       {**p, 'amount': game.price.amount_cents if game.price else None, 'free': game.free_to_play, 'observed': game.price.observed_at if game.price else None})
                    connection.execute(text('insert into capacity_game_embeddings values(:v,:id,:hash,cast(:vector as extensions.vector))'), {**p, 'hash': game.semantic_hash, 'vector': json.dumps(vector['vector'])})
                report['sequential_pilot_import_seconds'] = time.perf_counter() - started
                connection.execute(text('insert into capacity_analytics values(:v,cast(:doc as jsonb))'), {'v': version, 'doc': json.dumps(aggregate)})
                query_vector = vectors[0]['vector']
                for scale in (len(games), 500, 1000, 2000, 4000):
                    if scale > len(games):
                        connection.execute(text('TRUNCATE capacity_games,capacity_game_platforms,capacity_game_terms,capacity_game_prices,capacity_game_embeddings'))
                        # Real pilot document/vector distribution replicated under fixture-only IDs: not new eligible games.
                        for name in TABLES:
                            rows = []
                            if name == 'games':
                                for n in range(scale):
                                    g = games[n % len(games)]
                                    rows.append({'v': version, 'id': n + 1, 'title': g.title, 'nt': g.title.casefold(), 'description': g.description,
                                                 'eligible': g.eligibility, 'hash': g.semantic_hash, 'doc': json.dumps(documents[n % len(games)])})
                                connection.execute(text('insert into capacity_games(version,app_id,title,normalized_title,description,eligibility,semantic_hash,document) values(:v,:id,:title,:nt,:description,:eligible,:hash,cast(:doc as jsonb))'), rows)
                            else:
                                source_rows = []
                                for n in range(scale):
                                    g = games[n % len(games)]
                                    if name == 'game_platforms':
                                        source_rows.extend({'v': version, 'id': n + 1, 'platform': k, 'supported': v} for k, v in g.platforms.items())
                                    elif name == 'game_terms':
                                        source_rows.extend({'v': version, 'id': n + 1, 'kind': kind, 'term': term} for kind, labels in (('genre', g.genres), ('tag', g.tags), ('mode', g.modes)) for term in set(labels))
                                    elif name == 'game_prices':
                                        source_rows.append({'v': version, 'id': n + 1, 'amount': g.price.amount_cents if g.price else None, 'free': g.free_to_play, 'observed': g.price.observed_at if g.price else None})
                                    else:
                                        source_rows.append({'v': version, 'id': n + 1, 'hash': g.semantic_hash, 'vector': json.dumps(vectors[n % len(games)]['vector'])})
                                statements = {'game_platforms': 'values(:v,:id,:platform,:supported)', 'game_terms': 'values(:v,:id,:kind,:term)',
                                              'game_prices': "values(:v,:id,:amount,:free,'US','USD',:observed)", 'game_embeddings': 'values(:v,:id,:hash,cast(:vector as extensions.vector))'}
                                connection.execute(text(f'insert into capacity_{name} {statements[name]}'), source_rows)
                    for name in TABLES:
                        connection.execute(text(f'ANALYZE capacity_{name}'))
                    relations = {name: connection.execute(text('select pg_total_relation_size(cast(:name as regclass))'), {'name': f'pg_temp.capacity_{name}'}).scalar_one() for name in (*TABLES, 'analytics')}
                    connection.execute(text("SET LOCAL statement_timeout='2s'"))
                    timings = {}
                    for label, predicate in (('unfiltered', 'true'), ('windows_single_under_20', "p.amount_cents<=2000 and exists(select 1 from capacity_game_platforms s where s.version=g.version and s.app_id=g.app_id and s.platform='windows' and s.supported is true) and exists(select 1 from capacity_game_terms t where t.version=g.version and t.app_id=g.app_id and t.kind='mode' and t.term='single-player')"), ('mac_coop', "exists(select 1 from capacity_game_platforms s where s.version=g.version and s.app_id=g.app_id and s.platform='mac' and s.supported is true) and exists(select 1 from capacity_game_terms t where t.version=g.version and t.app_id=g.app_id and t.kind='mode' and t.term='online-co-op')")):
                        samples = []
                        statement = text(f"select g.app_id from capacity_games g join capacity_game_embeddings e using(version,app_id) left join capacity_game_prices p using(version,app_id) where g.version=:v and g.eligibility='eligible' and {predicate} order by e.embedding OPERATOR(extensions.<=>) cast(:vector as extensions.vector),g.app_id limit 20")
                        for _ in range(6):
                            started = time.perf_counter()
                            connection.execute(statement, {'v': version, 'vector': json.dumps(query_vector)}).all()
                            samples.append((time.perf_counter() - started) * 1000)
                        explain = connection.execute(text('EXPLAIN (ANALYZE,FORMAT JSON) ' + statement.text), {'v': version, 'vector': json.dumps(query_vector)}).scalar_one()
                        timings[label] = {**percentile(samples), 'server_execution_ms': explain[0]['Execution Time']}
                    report['scales'].append({'rows': scale, 'fixture_replication': scale != len(games), 'relations_bytes': relations, 'total_bytes': sum(relations.values()), 'exact_filtered_retrieval': timings})
                    write_json(output / 'measurement.json', report)
                    connection.execute(text("SET LOCAL statement_timeout='120s'"))
            finally:
                transaction.rollback()
            report['temp_relations_removed'] = connection.execute(text("select to_regclass('pg_temp.capacity_games') is null")).scalar_one()
    finally:
        engine.dispose()
    report['peak_working_set_bytes'] = psutil.Process().memory_info().peak_wset
    write_json(output / 'measurement.json', report)
    return {'pilot': len(games), 'scales': [s['rows'] for s in report['scales']], 'rollback': report['temp_relations_removed']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('snapshot', 'candidates', 'collect', 'reviews', 'measure', 'api-memory', 'self-check'))
    parser.add_argument('--env-file', type=Path, default=ROOT / 'backend/.env')
    parser.add_argument('--project-url', default='https://mmdmxjiawlbridvvhtrt.supabase.co')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/reports/catalog-capacity-2026-11-05')
    parser.add_argument('--pilot', type=Path, default=ROOT / 'data/fixtures/catalog-capacity-pilot.json')
    args = parser.parse_args()
    if args.phase == 'self-check':
        assert percentile([4, 1, 3, 2, 5, 6]) == {'samples': 6, 'p50_ms': 3, 'p95_ms': 6}
        assert steam_app_id('https://store.steampowered.com/app/620/') == 620
        assert not db_url_matches_project('postgresql://user:pw@wrong.example/db', args.project_url)
        print('self-check passed')
        return
    config = dotenv_values(args.env_file, interpolate=False)
    pilot = json.loads(args.pilot.read_text(encoding='utf-8'))
    args.output.mkdir(parents=True, exist_ok=True)
    if args.phase == 'snapshot':
        result = snapshot(config, args.project_url, args.output)
    elif args.phase == 'candidates':
        result = candidates(args.output, pilot)
    elif args.phase == 'collect':
        result = collect(args.output, pilot)
    elif args.phase == 'reviews':
        result = review_probe(args.output)
    elif args.phase == 'api-memory':
        result = api_memory(config, args.output)
    else:
        result = measure(config, args.project_url, args.output)
    print(json.dumps(result, default=str))
    if result.get('status', '').startswith('stopped'):
        raise SystemExit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__}), file=sys.stderr)
        raise SystemExit(1)
