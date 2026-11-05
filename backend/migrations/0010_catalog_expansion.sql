-- Additive only: legacy Game documents, prices, vectors, archives and usage are unchanged.
alter table discovery.games add column identity_title text;
alter table discovery.games add column compact_title text;
alter table discovery.games add column title_tokens text[];
create index games_identity_title_idx on discovery.games(version, identity_title);
create index games_compact_title_idx on discovery.games(version, compact_title);
alter table discovery.games add constraint games_identity_keys_consistent check (
    (identity_title is null and compact_title is null and title_tokens is null) or
    (identity_title is not null and compact_title=replace(identity_title,' ','') and title_tokens is not null)
);

alter table discovery.catalog_versions add column artifact_manifest jsonb
    check (artifact_manifest is null or pg_column_size(artifact_manifest)<=16384);

create table discovery.game_dashboard_metadata (
    version text not null,
    app_id integer not null,
    document jsonb not null check (pg_column_size(document)<=131072),
    primary key(version,app_id),
    foreign key(version,app_id) references discovery.games(version,app_id)
);
alter table discovery.game_dashboard_metadata enable row level security;
revoke all on discovery.game_dashboard_metadata from public,anon,authenticated;
grant select on discovery.game_dashboard_metadata to game_discovery_runtime;
create policy active_catalog_read on discovery.game_dashboard_metadata for select to game_discovery_runtime
    using(exists(select 1 from discovery.catalog_versions v where v.version=game_dashboard_metadata.version and v.active));

-- The Alembic online migration also backfills identity keys with Python NFKC/casefold.
-- Use the developer migration CLI, not this DDL fragment alone, for an existing catalog.
