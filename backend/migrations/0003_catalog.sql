-- Immutable, version-scoped catalog snapshots. No client writes or staged reads.
create schema if not exists extensions;
create extension if not exists vector with schema extensions;
grant usage on schema extensions to game_discovery_runtime;

create table discovery.games (
    version text not null references discovery.catalog_versions(version),
    app_id integer not null check (app_id > 0),
    title text not null check (length(title) between 1 and 300),
    normalized_title text not null,
    description text not null,
    eligibility text not null check (eligibility in ('eligible','excluded','quarantined')),
    semantic_hash text not null,
    document jsonb not null check (pg_column_size(document) <= 131072),
    search_text tsvector generated always as
        (to_tsvector('english', title || ' ' || description)) stored,
    primary key (version, app_id)
);
create index games_title_idx on discovery.games(version, normalized_title);
create index games_search_idx on discovery.games using gin(search_text);

create table discovery.game_platforms (
    version text not null,
    app_id integer not null,
    platform text not null check (platform in ('windows','mac','linux')),
    supported boolean,
    primary key (version, app_id, platform),
    foreign key (version, app_id) references discovery.games(version, app_id)
);
create table discovery.game_terms (
    version text not null,
    app_id integer not null,
    kind text not null check (kind in ('genre','tag','mode')),
    term text not null,
    primary key (version, app_id, kind, term),
    foreign key (version, app_id) references discovery.games(version, app_id)
);
create index game_terms_filter_idx on discovery.game_terms(version, kind, term, app_id);

create table discovery.game_prices (
    version text not null,
    app_id integer not null,
    amount_cents integer check (amount_cents >= 0),
    free_to_play boolean,
    region text not null check (region = 'US'),
    currency text not null check (currency = 'USD'),
    observed_at timestamptz,
    primary key (version, app_id),
    foreign key (version, app_id) references discovery.games(version, app_id)
);
create table discovery.game_embeddings (
    version text not null,
    app_id integer not null,
    semantic_hash text not null,
    embedding extensions.vector(384) not null,
    primary key (version, app_id),
    foreign key (version, app_id) references discovery.games(version, app_id)
);
-- Exact vector search first. An approximate index is not justified for this sample.
do $$ declare tbl text; begin
    foreach tbl in array array['games','game_platforms','game_terms','game_prices','game_embeddings'] loop
        execute format('alter table discovery.%I enable row level security', tbl);
        execute format('revoke all on discovery.%I from public', tbl);
        execute format('grant select on discovery.%I to game_discovery_runtime', tbl);
        execute format('create policy active_catalog_read on discovery.%I for select to game_discovery_runtime '
            || 'using (exists (select 1 from discovery.catalog_versions v where v.version = %I.version and v.active))', tbl, tbl);
    end loop;
end $$;
