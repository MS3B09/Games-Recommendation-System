-- Disposable private M0 experiment, not the activated application catalog.
-- Apply explicitly through Supabase migrations; the sizing job performs DML only.
create schema discovery_m0;
revoke all on schema discovery_m0 from public, anon, authenticated, service_role;

create table discovery_m0.runs (
    run_key text primary key,
    input_sha256 text not null,
    sample_limit integer not null check (sample_limit between 1 and 3000),
    created_at timestamptz not null default now(),
    purpose text not null check (purpose = 'storage_experiment_only')
);
create table discovery_m0.games (
    app_id bigint primary key check (app_id > 0),
    run_key text not null references discovery_m0.runs(run_key),
    title text not null,
    normalized_title text not null,
    description text not null,
    store_url text not null,
    artwork_url text,
    content_hash text not null,
    eligibility text not null check (eligibility = 'quarantined'),
    observed_at timestamptz,
    search_vector tsvector generated always as
      (to_tsvector('english'::regconfig, title || ' ' || description)) stored
);
create index m0_games_run_idx on discovery_m0.games(run_key);
create index m0_games_title_idx on discovery_m0.games(normalized_title);
create index m0_games_search_idx on discovery_m0.games using gin(search_vector);
create table discovery_m0.platforms (
    app_id bigint not null references discovery_m0.games(app_id),
    platform text not null check (platform in ('windows','macos','linux')),
    supported boolean,
    primary key (app_id, platform)
);
create index m0_platform_filter_idx on discovery_m0.platforms(platform, supported, app_id);
create table discovery_m0.terms (
    term_key text primary key,
    kind text not null,
    label text not null,
    provenance text not null check (provenance = 'synthetic_storage_fixture')
);
create table discovery_m0.game_terms (
    app_id bigint not null references discovery_m0.games(app_id),
    term_key text not null references discovery_m0.terms(term_key),
    primary key (app_id, term_key)
);
create index m0_term_filter_idx on discovery_m0.game_terms(term_key, app_id);
create table discovery_m0.prices (
    app_id bigint primary key references discovery_m0.games(app_id),
    amount_cents integer check (amount_cents >= 0),
    currency text,
    region text,
    is_free boolean,
    observed_at timestamptz
);
create index m0_price_filter_idx on discovery_m0.prices(region, currency, amount_cents);
create table discovery_m0.reviews (
    app_id bigint primary key references discovery_m0.games(app_id),
    positive_count bigint,
    total_count bigint,
    summary text,
    observed_at timestamptz,
    check (positive_count >= 0 and total_count >= positive_count)
);
create table discovery_m0.sources (
    app_id bigint primary key references discovery_m0.games(app_id),
    source_url text not null,
    collected_at timestamptz,
    snapshot_hash text not null
);
create table discovery_m0.evidence (
    app_id bigint not null references discovery_m0.sources(app_id),
    source_field text not null,
    excerpt text not null,
    primary key (app_id, source_field)
);
create table discovery_m0.embeddings (
    app_id bigint primary key references discovery_m0.games(app_id),
    model_revision text not null,
    content_hash text not null,
    embedding extensions.vector(384) not null,
    generated_at timestamptz not null default now()
);
-- Defense in depth even though this schema has no browser-role privileges.
alter table discovery_m0.runs enable row level security;
alter table discovery_m0.games enable row level security;
alter table discovery_m0.platforms enable row level security;
alter table discovery_m0.terms enable row level security;
alter table discovery_m0.game_terms enable row level security;
alter table discovery_m0.prices enable row level security;
alter table discovery_m0.reviews enable row level security;
alter table discovery_m0.sources enable row level security;
alter table discovery_m0.evidence enable row level security;
alter table discovery_m0.embeddings enable row level security;
revoke all on all tables in schema discovery_m0 from public, anon, authenticated, service_role;
comment on schema discovery_m0 is 'M0 sizing only: historical descriptions and synthetic taxonomy/vectors; never serve recommendations.';
