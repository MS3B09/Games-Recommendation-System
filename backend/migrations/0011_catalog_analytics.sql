-- Additive sidecar: original catalog manifests, version IDs and Game documents stay immutable.
alter table discovery.catalog_versions add column analytics_manifest jsonb
    check (analytics_manifest is null or (jsonb_typeof(analytics_manifest)='object' and pg_column_size(analytics_manifest)<=4096));

create table discovery.catalog_analytics (
    version text primary key references discovery.catalog_versions(version),
    sha256 text not null check (sha256 ~ '^[a-f0-9]{64}$'),
    document jsonb not null check (jsonb_typeof(document)='object' and pg_column_size(document)<=262144),
    check (document->>'catalog_version'=version and document->>'format'='catalog-analytics-v1')
);
alter table discovery.catalog_analytics enable row level security;
revoke all on discovery.catalog_analytics from public,anon,authenticated;
grant select on discovery.catalog_analytics to game_discovery_runtime;
create policy active_catalog_read on discovery.catalog_analytics for select to game_discovery_runtime
    using(exists(select 1 from discovery.catalog_versions v where v.version=catalog_analytics.version and v.active));

-- Defer until commit so aggregate attachment and catalog activation remain one atomic operation.
create function discovery.check_active_analytics() returns trigger language plpgsql
set search_path = pg_catalog, discovery as $$
begin
    if exists(select 1 from discovery.catalog_versions v left join discovery.catalog_analytics a using(version)
        where v.active and v.analytics_manifest is not null and (
            a.version is null or a.sha256 is distinct from v.analytics_manifest->>'sha256'
            or v.version is distinct from v.analytics_manifest->>'catalog_version'
            or 'catalog-analytics-v1' is distinct from v.analytics_manifest->>'format'
            or v.artifact_manifest->>'games_sha256' is distinct from v.analytics_manifest->>'games_sha256'
            or v.artifact_manifest->>'metadata_sha256' is distinct from v.analytics_manifest->>'metadata_sha256'
            or v.artifact_manifest->>'artifact_sha256' is distinct from v.analytics_manifest->>'artifact_sha256'
            or v.game_count is distinct from (a.document->>'total_games')::integer)) then
        raise check_violation using message='Active catalog analytics identity mismatch';
    end if;
    return null;
end $$;
revoke all on function discovery.check_active_analytics() from public,anon,authenticated;
create constraint trigger active_analytics_version after insert or update on discovery.catalog_versions
    deferrable initially deferred for each row execute function discovery.check_active_analytics();
create constraint trigger active_analytics_document after insert or update or delete on discovery.catalog_analytics
    deferrable initially deferred for each row execute function discovery.check_active_analytics();
