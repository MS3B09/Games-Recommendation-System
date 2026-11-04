-- Guest conversations: capability-only execute access; no browser table grants.
create table discovery.conversation_archives (
    id uuid primary key,
    secret_hash text not null check (secret_hash ~ '^[0-9a-f]{64}$'),
    revision integer not null default 0 check (revision >= 0),
    document jsonb not null default '{"events":[],"memory":{}}'::jsonb,
    pending uuid,
    lease_until timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (jsonb_typeof(document->'events') = 'array'),
    check (jsonb_typeof(document->'memory') = 'object'),
    check (octet_length(document::text) <= 4194304)
);
alter table discovery.conversation_archives enable row level security;
revoke all on discovery.conversation_archives from public, anon, authenticated, game_discovery_runtime;

create function discovery.conversation_create(cid uuid, secret text, initial_events jsonb default '[]'::jsonb) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
    perform pg_catalog.pg_advisory_xact_lock(1834001);
    if secret is null or secret !~ '^[0-9a-f]{64}$' then return false; end if;
    if jsonb_typeof(initial_events)<>'array' or jsonb_array_length(initial_events)>20 or octet_length(initial_events::text)>262144 then return false; end if;
    if (select count(*) from discovery.conversation_archives) >= 1000 or
       (select coalesce(sum(octet_length(document::text)),0) from discovery.conversation_archives) > 33292288
    then return false; end if;
    insert into discovery.conversation_archives(id,secret_hash,revision,document)
        values(cid,secret,jsonb_array_length(initial_events),jsonb_build_object('events',initial_events,'memory','{}'::jsonb));
    return true;
end;
$$;

create function discovery.conversation_read(cid uuid, secret text) returns jsonb
language sql security definer set search_path = '' as $$
    select jsonb_build_object('revision',revision,'document',document)
    from discovery.conversation_archives where id=cid and secret_hash=secret;
$$;

create function discovery.conversation_begin(cid uuid, secret text, rid uuid, expected integer, message text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare c discovery.conversation_archives%rowtype; e jsonb; n integer;
begin
    perform pg_catalog.pg_advisory_xact_lock(1834001);
    if rid is null or expected is null then return jsonb_build_object('error','invalid_input'); end if;
    select * into c from discovery.conversation_archives where id=cid and secret_hash=secret for update;
    if not found then return jsonb_build_object('error','chat_session_missing'); end if;
    for e in select value from pg_catalog.jsonb_array_elements(c.document->'events') loop
        if e->>'id'=rid::text and e->>'status'='done' then
            if e->>'input' is distinct from message then return jsonb_build_object('error','chat_session_conflict'); end if;
            return jsonb_build_object('cached',e->'output','revision',c.revision);
        end if;
    end loop;
    if c.pending is not null and c.lease_until > pg_catalog.clock_timestamp() then
        return jsonb_build_object('error','chat_busy');
    end if;
    if c.revision <> expected then return jsonb_build_object('error','chat_session_conflict'); end if;
    if message is null or length(message)<1 or length(message)>2000 then
        return jsonb_build_object('error','invalid_input');
    end if;
    if octet_length(c.document::text)>3932160 or
       (select coalesce(sum(octet_length(document::text)),0) from discovery.conversation_archives)>33292288
    then return jsonb_build_object('error','chat_archive_full'); end if;
    -- Expired interrupted attempts remain in the original archive.
    if c.pending is not null then
        n := jsonb_array_length(c.document->'events')-1;
        c.document := jsonb_set(c.document,array['events',n::text,'status'],'"interrupted"'::jsonb);
    end if;
    e := jsonb_build_object('id',rid,'input',message,'status','pending','at',pg_catalog.clock_timestamp(),
                            'attempts','[]'::jsonb);
    n := jsonb_array_length(c.document->'events')-1;
    if n>=0 and c.document->'events'->n->>'id'=rid::text then
        if c.document->'events'->n->>'input' is distinct from message then
            return jsonb_build_object('error','chat_session_conflict');
        end if;
        c.document := jsonb_set(c.document,array['events',n::text,'status'],'"pending"'::jsonb);
    else
        c.document := jsonb_set(c.document,'{events}',(c.document->'events') || jsonb_build_array(e));
    end if;
    update discovery.conversation_archives set document=c.document,pending=rid,
        lease_until=pg_catalog.clock_timestamp()+interval '5 minutes',updated_at=pg_catalog.clock_timestamp() where id=cid;
    return jsonb_build_object('revision',c.revision,'document',c.document);
end;
$$;

create function discovery.conversation_finish(cid uuid, secret text, rid uuid, result jsonb, working_memory jsonb, trace jsonb)
returns boolean language plpgsql security definer set search_path = '' as $$
declare c discovery.conversation_archives%rowtype; n integer; e jsonb; d jsonb;
begin
    perform pg_catalog.pg_advisory_xact_lock(1834001);
    select * into c from discovery.conversation_archives where id=cid and secret_hash=secret for update;
    if not found or c.pending is distinct from rid then return false; end if;
    n := jsonb_array_length(c.document->'events')-1;
    e := c.document->'events'->n;
    if e->>'id'<>rid::text then return false; end if;
    e := e || jsonb_build_object('status',case when result is null then 'failed' else 'done' end,
        'output',result,'attempts',(e->'attempts') || jsonb_build_array(jsonb_build_object(
            'at',pg_catalog.clock_timestamp(),'trace',trace,'succeeded',result is not null)));
    d := jsonb_set(c.document,array['events',n::text],e);
    if result is not null then
        if jsonb_typeof(working_memory)<>'object' then return false; end if;
        d := jsonb_set(d,'{memory}',working_memory);
    end if;
    if octet_length(d::text)>4194304 or
       (select coalesce(sum(octet_length(document::text)),0) from discovery.conversation_archives where id<>cid)
            +octet_length(d::text)>33554432 then return false; end if;
    update discovery.conversation_archives set document=d,pending=null,lease_until=null,
        revision=revision+case when result is null then 0 else 1 end,updated_at=pg_catalog.clock_timestamp() where id=cid;
    return true;
end;
$$;

create function discovery.conversation_delete(cid uuid, secret text) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
    delete from discovery.conversation_archives where id=cid and secret_hash=secret;
    return found;
end;
$$;

revoke all on function discovery.conversation_create(uuid,text,jsonb), discovery.conversation_read(uuid,text),
 discovery.conversation_begin(uuid,text,uuid,integer,text), discovery.conversation_finish(uuid,text,uuid,jsonb,jsonb,jsonb),
 discovery.conversation_delete(uuid,text) from public, anon, authenticated;
grant execute on function discovery.conversation_create(uuid,text,jsonb), discovery.conversation_read(uuid,text),
 discovery.conversation_begin(uuid,text,uuid,integer,text), discovery.conversation_finish(uuid,text,uuid,jsonb,jsonb,jsonb),
 discovery.conversation_delete(uuid,text) to game_discovery_runtime;
