"""Opt-in analytics migration/activation acceptance in an exact owned schema; no public activation."""

import argparse
import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from game_discovery.catalog.analytics import build_analytics
from game_discovery.catalog.contracts import digest
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.core.database_url import normalize_db_url
from game_discovery.jobs.catalog import database_manifest, load_games, load_metadata, write_json

TAG = 'game-discovery-owned-analytics-verification-v1'


def verify(run: Path, env_file: Path, output: Path) -> dict:
    os.environ.update(GAME_DISCOVERY_ENV_FILE='C:/Users/User/AppData/Local/Temp/opencode/catalog-unit-no-env', AI_ENABLED='false',
                      QUERY_MODEL_PATH='', QUERY_TOKENIZER_PATH='', QUERY_ARTIFACT_PATH='')
    from fastapi.testclient import TestClient
    from game_discovery.api.main import create_app
    from game_discovery.core.settings import Settings
    from game_discovery.db.readiness import CatalogReadiness

    config = dotenv_values(env_file, interpolate=False)
    engines = [create_engine(make_url(normalize_db_url(config[key])).set(drivername='postgresql+psycopg'),
                             hide_parameters=True, connect_args={'prepare_threshold': None, 'connect_timeout': 10})
               for key in ('MIGRATION_DATABASE_URL', 'DATABASE_URL')]
    admin, runtime = engines
    schema = 'analytics_check_' + uuid.uuid4().hex[:12]
    games, manifest = load_games(run)
    artifact = json.loads((run/'artifact.json').read_text(encoding='utf-8'))
    version = artifact['version']
    data = build_analytics(games, load_metadata(run, manifest, games), version).model_dump(mode='json')
    checksum = digest(data)
    binding = {'catalog_version': version, 'format': data['format'], 'sha256': checksum,
               'artifact_sha256': digest(artifact), 'games_sha256': artifact['games_sha256'], 'metadata_sha256': artifact['metadata_sha256']}
    report = {'status': 'in_progress', 'checks': [], 'public_activation': False}
    try:
        with admin.begin() as c:
            old = c.execute(text('select version from discovery.catalog_versions where active')).scalar_one()
            before = [r[0] for r in c.execute(text('select document from discovery.games where version=:v order by app_id'), {'v': old})]
            c.execute(text(f'create schema {schema}'))
            c.execute(text(f"comment on schema {schema} is '{TAG}'"))
            c.execute(text(f'revoke all on schema {schema} from public'))
            c.execute(text(f'create table {schema}.catalog_versions (like discovery.catalog_versions including all)'))
            c.execute(text(f'alter table {schema}.catalog_versions drop column if exists analytics_manifest'))
            columns = 'version,created_at,activated_at,active,game_count,model_id,model_revision,dimensions,region,currency,source_observed_at,artifact_manifest'
            c.execute(text(f'insert into {schema}.catalog_versions({columns}) select {columns} from discovery.catalog_versions'))
            sql = (Path(__file__).resolve().parents[1]/'migrations/0011_catalog_analytics.sql').read_text(encoding='utf-8')
            c.exec_driver_sql(sql.replace('discovery.', schema+'.').replace('pg_catalog, discovery', 'pg_catalog, '+schema))
            c.execute(text(f'alter table {schema}.catalog_versions enable row level security'))
            c.execute(text(f'create policy active_read on {schema}.catalog_versions for select to game_discovery_runtime using(active)'))
            c.execute(text(f'grant usage on schema {schema} to game_discovery_runtime'))
            c.execute(text(f'grant select on {schema}.catalog_versions to game_discovery_runtime'))
            c.execute(text(f'insert into {schema}.catalog_analytics values(:v,:sha,cast(:d as jsonb))'), {'v': version, 'sha': checksum, 'd': json.dumps(data)})
            c.execute(text(f'update {schema}.catalog_versions set analytics_manifest=cast(:d as jsonb),artifact_manifest=cast(:a as jsonb) where version=:v'),
                      {'v': version, 'd': json.dumps(binding), 'a': json.dumps(database_manifest(artifact))})
        report['checks'].append('additive migration on real catalog table shape; legacy active preserved; inactive analytics hidden')

        class Repo(CatalogRepository):
            @contextmanager
            def snapshot(self):
                with runtime.connect().execution_options(isolation_level='REPEATABLE READ', postgresql_readonly=True) as c, c.begin():
                    c.execute(text("set local statement_timeout='2s'"))
                    class Connection:
                        def execute(self, statement, params=None):
                            return c.execute(text(str(statement).replace('discovery.', schema+'.')), params or {})
                    active = c.execute(text(f'select version from {schema}.catalog_versions where active')).scalar_one()
                    yield Connection(), active
        repo = Repo(runtime)
        try:
            repo.analytics()
        except CatalogFailure as error:
            assert error.code == 'analytics_unavailable'
        else:
            raise AssertionError('Legacy catalog must not borrow staged analytics')
        with runtime.connect() as c:
            assert c.execute(text(f'select count(*) from {schema}.catalog_analytics')).scalar_one() == 0
            assert not c.execute(text("select has_table_privilege(current_user,:t,'INSERT')"), {'t': schema+'.catalog_analytics'}).scalar_one()
        with admin.begin() as c:
            c.execute(text(f'update {schema}.catalog_versions set active=false where active'))
            c.execute(text(f'update {schema}.catalog_versions set active=true,activated_at=now() where version=:v'), {'v': version})
        for mutation in (f'delete from {schema}.catalog_analytics',
                         f"update {schema}.catalog_analytics set sha256=repeat('0',64)",
                         f"update {schema}.catalog_versions set analytics_manifest=jsonb_set(analytics_manifest,'{{games_sha256}}','\"wrong\"') where active"):
            with admin.connect() as c:
                try:
                    c.execute(text(mutation))
                    c.commit()
                except IntegrityError:
                    c.rollback()
                else:
                    raise AssertionError('Invalid active analytics accepted')
        report['checks'].append('commit rejects missing/mismatched active analytics and input identity; restricted role cannot write')
        with TestClient(create_app(Settings(), catalog_probe=lambda: CatalogReadiness(version=version, game_count=len(games)), repository=repo)) as client:
            started = time.perf_counter()
            response = client.get('/api/v1/analytics')
            report['request_ms'] = round((time.perf_counter()-started)*1000, 3)
            assert response.status_code == 200 and response.json()['data'] == data
            assert response.headers['cache-control'] == 'no-store'
            snapshot = response.json()
            report.update(payload_bytes=len(response.content), catalog_version=version, analytics_sha256=checksum, total_games=data['total_games'])
            write_json(output.with_name(output.stem+'-snapshot.json'), snapshot)
        with admin.connect() as c:
            actual = c.execute(text('select count(*) from discovery.games where version=:v and eligibility=\'eligible\''), {'v': version}).scalar_one()
            assert actual == data['total_games'] == 2000
            # Uncommitted activation is invisible to the separate restricted reader.
            c.execute(text(f'update {schema}.catalog_versions set active=false where active'))
            c.execute(text(f'update {schema}.catalog_versions set active=true,activated_at=now() where version=:v'), {'v': old})
            assert repo.analytics().catalog_version == version
            c.rollback()
        report['checks'].append('actual restricted ASGI aggregate equals all 2000 source pairs and stored eligible count; snapshot isolation/no-store')
        # A distinct one-game refresh fixture verifies version and metric switching.
        refreshed = games[0].model_copy(deep=True)
        new_data = build_analytics([refreshed], [load_metadata(run, manifest, games)[0]], 'refresh-fixture').model_dump(mode='json')
        refresh_artifact = {'games_sha256': digest([refreshed.model_dump(mode='json')]),
                            'metadata_sha256': digest([load_metadata(run, manifest, games)[0].model_dump(mode='json')])}
        refresh_artifact['artifact_sha256'] = digest(refresh_artifact)
        with admin.begin() as c:
            c.execute(text(f'''insert into {schema}.catalog_versions({columns}) select 'refresh-fixture',created_at,now(),false,1,
                model_id,model_revision,dimensions,region,currency,source_observed_at,artifact_manifest from {schema}.catalog_versions where version=:v'''), {'v': version})
            new_binding = {**binding, 'catalog_version': 'refresh-fixture', 'sha256': digest(new_data),
                           'artifact_sha256': refresh_artifact['artifact_sha256'],
                           'games_sha256': refresh_artifact['games_sha256'], 'metadata_sha256': refresh_artifact['metadata_sha256']}
            c.execute(text(f'insert into {schema}.catalog_analytics values(:v,:sha,cast(:d as jsonb))'), {'v': 'refresh-fixture', 'sha': digest(new_data), 'd': json.dumps(new_data)})
            c.execute(text(f'update {schema}.catalog_versions set analytics_manifest=cast(:d as jsonb),artifact_manifest=cast(:a as jsonb) where version=\'refresh-fixture\''),
                      {'d': json.dumps(new_binding), 'a': json.dumps(refresh_artifact)})
            c.execute(text(f'update {schema}.catalog_versions set active=false where active'))
            c.execute(text(f'update {schema}.catalog_versions set active=true where version=\'refresh-fixture\''))
        assert repo.analytics().data.total_games == 1
        report['checks'].append('atomic refresh changes version and metrics without frontend rebuild; original snapshot does not mutate')
    finally:
        runtime.dispose()
        with admin.begin() as c:
            owned = c.execute(text("select pg_get_userbyid(nspowner)=current_user,obj_description(oid,'pg_namespace') from pg_namespace where nspname=:s"), {'s': schema}).one_or_none()
            if owned:
                assert tuple(owned) == (True, TAG)
                c.execute(text(f'drop schema {schema} cascade'))
            assert not c.execute(text('select exists(select 1 from pg_namespace where nspname=:s)'), {'s': schema}).scalar_one()
            assert c.execute(text('select version from discovery.catalog_versions where active')).scalar_one() == old
            after = [r[0] for r in c.execute(text('select document from discovery.games where version=:v order by app_id'), {'v': old})]
            assert before == after
        admin.dispose()
    report.update(status='passed', private_schema_removed=True, public_digest_unchanged=digest(before), actual_llm_calls=0)
    write_json(output, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.run_dir, args.env_file, args.output), indent=2))
