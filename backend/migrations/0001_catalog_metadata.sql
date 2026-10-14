-- M1 metadata foundation. Apply explicitly, never during API startup.
create schema discovery;
revoke all on schema discovery from public;

create role game_discovery_runtime login nosuperuser nocreatedb nocreaterole noinherit nobypassrls connection limit 5;
alter role game_discovery_runtime set statement_timeout = '5s';
alter role game_discovery_runtime set lock_timeout = '2s';

create table discovery.catalog_versions (
    version text primary key,
    created_at timestamptz not null default now(),
    activated_at timestamptz,
    active boolean not null default false,
    game_count integer not null check (game_count >= 0),
    model_id text not null,
    model_revision text not null,
    dimensions integer not null check (dimensions = 384),
    region text not null check (region = 'US'),
    currency text not null check (currency = 'USD'),
    source_observed_at timestamptz,
    check (not active or (activated_at is not null and game_count > 0))
);
create unique index catalog_single_active_version_idx on discovery.catalog_versions(active) where active;
alter table discovery.catalog_versions enable row level security;
create policy catalog_metadata_runtime_read on discovery.catalog_versions
    for select to game_discovery_runtime using (true);

create table discovery.job_runs (
    id uuid primary key default gen_random_uuid(),
    kind text not null,
    status text not null check (status in ('running','complete','failed')),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    summary jsonb not null default '{}'::jsonb,
    check (pg_column_size(summary) <= 16384)
);
create index job_runs_started_at_idx on discovery.job_runs(started_at);
alter table discovery.job_runs enable row level security;
-- Explicit deny-all policy: runtime/browser roles do not read developer job logs.
create policy job_runs_no_client_access on discovery.job_runs for all to public using (false) with check (false);

-- Also portable to native PostgreSQL, where Supabase's browser roles/schema do not exist.
do $$ declare browser_role text; begin
    foreach browser_role in array array['anon', 'authenticated', 'service_role'] loop
        if exists (select 1 from pg_roles where rolname=browser_role) then
            execute format('revoke all on schema discovery from %I', browser_role);
            execute format('revoke all on all tables in schema discovery from %I', browser_role);
        end if;
    end loop;
end $$;
revoke all on all tables in schema discovery from public;
grant usage on schema discovery to game_discovery_runtime;
grant select on discovery.catalog_versions to game_discovery_runtime;
