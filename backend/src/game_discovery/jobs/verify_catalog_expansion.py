"""Owned private-schema migration/title/metadata check; no public activation or inference."""

import argparse
import json
import uuid
from contextlib import contextmanager
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from game_discovery.catalog.contracts import Game, digest, semantic_hash
from game_discovery.catalog.metadata import normalize_metadata
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.core.database_url import normalize_db_url
from game_discovery.jobs.catalog import write_json
from game_discovery.retrieval.titles import normalize_title


def verify(env_file: Path, output: Path) -> dict:
    config = dotenv_values(env_file, interpolate=False)
    raw_url = config.get('MIGRATION_DATABASE_URL')
    if not raw_url:
        raise ValueError('Configure developer database access locally')
    engine = create_engine(make_url(normalize_db_url(raw_url)).set(drivername='postgresql+psycopg'),
                           hide_parameters=True, connect_args={'prepare_threshold': None, 'connect_timeout': 10})
    runtime_engine = create_engine(make_url(normalize_db_url(config['DATABASE_URL'])).set(drivername='postgresql+psycopg'),
                                   hide_parameters=True, connect_args={'prepare_threshold': None, 'connect_timeout': 10})
    schema = 'catalog_check_' + uuid.uuid4().hex[:12]
    report = {'schema': schema, 'checks': []}
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            created = False
            reader = None
            try:
                connection.execute(text("SET LOCAL statement_timeout='120s'"))
                before = [row[0] for row in connection.execute(text('select document from discovery.games where version in (select version from discovery.catalog_versions where active) order by app_id'))]
                version = connection.execute(text('select version from discovery.catalog_versions where active')).scalar_one()
                connection.execute(text(f'create schema {schema}'))
                created = True
                connection.execute(text(f"comment on schema {schema} is 'game-discovery-owned-expansion-check-v1'"))
                connection.execute(text(f'revoke all on schema {schema} from public'))
                for name in ('catalog_versions', 'games'):
                    connection.execute(text(f'create table {schema}.{name} (like discovery.{name} including all)'))
                connection.execute(text(f'insert into {schema}.catalog_versions select * from discovery.catalog_versions'))
                # Reproduce the pre-migration shape even after the real additive upgrade.
                connection.execute(text(f'alter table {schema}.catalog_versions drop column if exists artifact_manifest'))
                for column in ('identity_title', 'compact_title', 'title_tokens'):
                    connection.execute(text(f'alter table {schema}.games drop column if exists {column} cascade'))
                columns = 'version,app_id,title,normalized_title,description,eligibility,semantic_hash,document'
                connection.execute(text(f'insert into {schema}.games({columns}) select {columns} from discovery.games'))
                migration = Path(__file__).resolve().parents[3] / 'migrations/0010_catalog_expansion.sql'
                connection.exec_driver_sql(migration.read_text(encoding='utf-8').replace('discovery.', schema + '.'))
                source = Game.model_validate(before[0])
                for index in range(301):
                    game = source.model_copy(deep=True)
                    game.app_id = 1000000000 + index
                    game.title = 'Straße Café – Beyond 256' if index == 300 else f'Capacity fixture chapter {index}'
                    game.semantic_hash = semantic_hash(game)
                    game = Game.model_validate(game.model_dump())
                    connection.execute(text(f'''insert into {schema}.games({columns})
                        values(:v,:id,:title,:normalized,:description,'eligible',:hash,cast(:doc as jsonb))'''),
                        {'v': version, 'id': game.app_id, 'title': game.title, 'normalized': game.title.casefold(),
                         'description': game.description, 'hash': game.semantic_hash, 'doc': game.model_dump_json()})
                for app_id, title in connection.execute(text(f'select app_id,title from {schema}.games where version=:v'), {'v': version}):
                    normalized = normalize_title(title)
                    connection.execute(text(f'update {schema}.games set identity_title=:title,compact_title=:compact,title_tokens=:tokens where version=:v and app_id=:id'),
                                       {'v': version, 'id': app_id, 'title': normalized, 'compact': normalized.replace(' ', ''), 'tokens': normalized.split()})
                metadata = normalize_metadata(source.app_id, {'developers': ['Thekla, Inc.'], 'release_date': {'date': '2020'}}, source.evidence[0].source)
                connection.execute(text(f'insert into {schema}.game_dashboard_metadata values(:v,:id,cast(:doc as jsonb))'),
                                   {'v': version, 'id': source.app_id, 'doc': metadata.model_dump_json()})
                staged = version + '-private-check'
                connection.execute(text(f'''insert into {schema}.catalog_versions(version,active,game_count,model_id,model_revision,dimensions,region,currency)
                    select :staged,false,1,model_id,model_revision,dimensions,region,currency from {schema}.catalog_versions where version=:v'''), {'staged': staged, 'v': version})
                connection.execute(text(f'''insert into {schema}.games({columns})
                    select :staged,app_id,title,normalized_title,description,eligibility,semantic_hash,document from {schema}.games where version=:v and app_id=:id'''),
                    {'staged': staged, 'v': version, 'id': source.app_id})
                connection.execute(text(f'insert into {schema}.game_dashboard_metadata values(:v,:id,cast(:doc as jsonb))'),
                                   {'v': staged, 'id': source.app_id, 'doc': metadata.model_dump_json()})
                connection.execute(text(f'grant usage on schema {schema} to game_discovery_runtime'))
                for name in ('catalog_versions', 'games'):
                    connection.execute(text(f'alter table {schema}.{name} enable row level security'))
                    connection.execute(text(f'grant select on {schema}.{name} to game_discovery_runtime'))
                connection.execute(text(f'create policy active_read on {schema}.catalog_versions for select to game_discovery_runtime using(active)'))
                connection.execute(text(f'''create policy active_read on {schema}.games for select to game_discovery_runtime
                    using(exists(select 1 from {schema}.catalog_versions v where v.version=games.version and v.active))'''))
                # Developer is deliberately not a member of the serving role. A separate
                # restricted connection needs committed, isolated fixtures, then exact cleanup.
                transaction.commit()
                reader = runtime_engine.connect().execution_options(postgresql_readonly=True)
                reader.execute(text("SET LOCAL statement_timeout='2s'"))

                class ScopedConnection:
                    def execute(self, statement, params=None):
                        return reader.execute(text(str(statement).replace('discovery.', schema + '.')), params or {})

                class ScopedRepository(CatalogRepository):
                    @contextmanager
                    def snapshot(self):
                        yield ScopedConnection(), version

                repository = ScopedRepository(engine)
                expected = {'Portal': [400], 'Portal-2': [620], 'spiderman': [1817070],
                            'STRASSE CAFÉ BEYOND 256': [1000000300]}
                for query, ids in expected.items():
                    result = repository.chat_title(query)
                    assert [game.app_id for game in result.games] == ids, query
                assert repository.chat_title('ori').match.kind == 'ambiguous'
                assert repository.chat_title('zzzzzz-no-such-title').match.kind == 'not_in_catalog'
                assert repository.chat_title('', 1000000300).games[0].app_id == 1000000300
                report['checks'].append('complete normalized/exact/reference matching beyond 256, alias and ambiguity')
                active = reader.execute(text(f'select count(*) from {schema}.game_dashboard_metadata where version=:v'), {'v': version}).scalar_one()
                inactive = reader.execute(text(f'select count(*) from {schema}.game_dashboard_metadata where version=:v'), {'v': staged}).scalar_one()
                assert active == 1 and inactive == 0
                assert not reader.execute(text("select rolsuper or rolcreatedb or rolcreaterole or rolbypassrls from pg_roles where rolname=current_user")).scalar_one()
                assert not reader.execute(text('select has_table_privilege(current_user,:table,\'INSERT\')'), {'table': schema + '.game_dashboard_metadata'}).scalar_one()
                report['checks'].append('restricted active-only metadata read; inactive hidden and writes denied')
                connection.execute(text(f'update {schema}.games set identity_title=null,compact_title=null,title_tokens=null where version=:v and app_id=1000000300'), {'v': version})
                connection.commit()
                try:
                    repository.chat_title('missing')
                except CatalogFailure as error:
                    assert error.code == 'catalog_identity_keys_unavailable'
                else:
                    raise AssertionError('Incomplete identities falsely established absence')
                report['checks'].append('missing identity keys fail closed')
                report['fixture_rows'] = len(before) + 301
            finally:
                if reader is not None:
                    reader.close()
                connection.rollback()
                if created:
                    owned = connection.execute(text("""select pg_get_userbyid(nspowner)=current_user,
                        obj_description(oid,'pg_namespace') from pg_namespace where nspname=:schema"""), {'schema': schema}).one_or_none()
                    if owned is not None:
                        if tuple(owned) != (True, 'game-discovery-owned-expansion-check-v1'):
                            raise ValueError('Scratch ownership mismatch; refusing cleanup')
                        connection.execute(text(f'drop schema {schema} cascade'))
                        connection.commit()
            assert not connection.execute(text('select exists(select 1 from pg_namespace where nspname=:schema)'), {'schema': schema}).scalar_one()
            after = [row[0] for row in connection.execute(text('select document from discovery.games where version in (select version from discovery.catalog_versions where active) order by app_id'))]
            assert before == after
            report.update(status='passed', private_schema_removed=True, public_catalog_unchanged=True,
                          active_documents_sha256=digest(after))
        write_json(output, report)
        return report
    finally:
        engine.dispose()
        runtime_engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.env_file, args.output)))
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__}))
        raise SystemExit(1)
