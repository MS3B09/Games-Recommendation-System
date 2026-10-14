-- Remove only the agent-created experiment after saving its measurements.
do $$
begin
    if (select obj_description(oid, 'pg_namespace') from pg_namespace where nspname = 'discovery_m0')
       is distinct from 'M0 sizing only: historical descriptions and synthetic taxonomy/vectors; never serve recommendations.' then
        raise exception 'Refusing cleanup: unexpected schema marker';
    end if;
    if (select count(*) from pg_tables where schemaname = 'discovery_m0') <> 10
       or exists (select 1 from discovery_m0.runs where purpose <> 'storage_experiment_only' or run_key <> 'm0-storage-v1') then
        raise exception 'Refusing cleanup: unexpected sizing objects';
    end if;
end $$;
drop schema discovery_m0 cascade;
