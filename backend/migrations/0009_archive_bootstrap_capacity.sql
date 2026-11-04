-- Retained legacy caches can contain up to 500k characters of canonical cards.
-- Admit bounded imports without exceeding the archive's shared logical ceiling.
create or replace function discovery.conversation_create(cid uuid, secret text, initial_events jsonb default '[]'::jsonb)
returns boolean language plpgsql security definer set search_path = '' as $$
declare initial_document jsonb;
begin
    perform pg_catalog.pg_advisory_xact_lock(1834001);
    if secret is null or secret !~ '^[0-9a-f]{64}$' then return false; end if;
    if jsonb_typeof(initial_events)<>'array' or jsonb_array_length(initial_events)>20
       or octet_length(initial_events::text)>1048576 then return false; end if;
    initial_document := jsonb_build_object('events',initial_events,'memory','{}'::jsonb);
    if (select count(*) from discovery.conversation_archives)>=1000 or
       (select coalesce(sum(octet_length(document::text)),0) from discovery.conversation_archives)
          +octet_length(initial_document::text)>33554432 then return false; end if;
    insert into discovery.conversation_archives(id,secret_hash,revision,document)
        values(cid,secret,jsonb_array_length(initial_events),initial_document);
    return true;
end;
$$;
revoke all on function discovery.conversation_create(uuid,text,jsonb) from public,anon,authenticated;
grant execute on function discovery.conversation_create(uuid,text,jsonb) to game_discovery_runtime;
create policy conversation_archives_private on discovery.conversation_archives
    for all to public using (false) with check (false);
