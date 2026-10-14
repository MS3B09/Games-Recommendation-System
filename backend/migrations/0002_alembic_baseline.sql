-- Existing Supabase project only: adopt the verified, already-applied M1 baseline.
-- Fresh native/project setups use `python -m game_discovery.db.migrate upgrade`.
do $$ begin
    if to_regclass('discovery.catalog_versions') is null or to_regclass('discovery.job_runs') is null then
        raise exception 'Initial metadata schema absent';
    end if;
    if (select count(*) from information_schema.columns where table_schema='discovery' and table_name='catalog_versions') <> 11
       or (select count(*) from information_schema.columns where table_schema='discovery' and table_name='job_runs') <> 6 then
        raise exception 'Metadata schema drift; inspect before baseline adoption';
    end if;
    if exists (select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
               where n.nspname='discovery' and c.relkind='r' and not c.relrowsecurity) then
        raise exception 'Metadata RLS missing';
    end if;
    if not has_table_privilege('game_discovery_runtime','discovery.catalog_versions','SELECT')
       or has_table_privilege('game_discovery_runtime','discovery.catalog_versions','INSERT')
       or has_table_privilege('game_discovery_runtime','discovery.job_runs','SELECT') then
        raise exception 'Runtime grants differ from baseline';
    end if;
end $$;
create schema discovery_migrations;
revoke all on schema discovery_migrations from public, anon, authenticated, service_role, game_discovery_runtime;
create table discovery_migrations.alembic_version (version_num varchar(32) primary key);
revoke all on discovery_migrations.alembic_version from public, anon, authenticated, service_role, game_discovery_runtime;
alter table discovery_migrations.alembic_version enable row level security;
create policy alembic_no_client_access on discovery_migrations.alembic_version for all to public using(false) with check(false);
insert into discovery_migrations.alembic_version(version_num) values ('0001');
