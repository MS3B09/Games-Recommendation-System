-- Temporary owner-approved R4 ceiling; never reset or refund consumed usage.
alter table discovery.ai_usage_windows
    drop constraint ai_usage_windows_calls_check,
    add constraint ai_usage_windows_calls_check check (calls between 0 and 100),
    drop constraint ai_usage_windows_reserved_tokens_check,
    add constraint ai_usage_windows_reserved_tokens_check check (reserved_tokens between 0 and 1500000);

create or replace function discovery.reserve_ai_usage(tokens integer, call_limit integer, token_limit integer)
returns boolean language plpgsql security definer set search_path = '' as $$
declare
    granted boolean;
    utc_day date := (pg_catalog.clock_timestamp() at time zone 'UTC')::date;
    utc_minute timestamptz := pg_catalog.date_trunc('minute', pg_catalog.clock_timestamp());
begin
    if tokens is null or tokens < 1 or tokens > 16000
       or call_limit is null or call_limit < 1 or call_limit > 100
       or token_limit is null or token_limit < 1 or token_limit > 1500000 or tokens > token_limit then
        return false;
    end if;
    insert into discovery.ai_usage_windows(id, day, calls, reserved_tokens, minute, minute_calls)
    values(true, utc_day, 1, tokens, utc_minute, 1)
    on conflict(id) do update set
        day = excluded.day,
        calls = case when ai_usage_windows.day = excluded.day then ai_usage_windows.calls + 1 else 1 end,
        reserved_tokens = case when ai_usage_windows.day = excluded.day then ai_usage_windows.reserved_tokens + excluded.reserved_tokens else excluded.reserved_tokens end,
        minute = excluded.minute,
        minute_calls = case when ai_usage_windows.minute = excluded.minute then ai_usage_windows.minute_calls + 1 else 1 end
    where (case when ai_usage_windows.day = excluded.day then ai_usage_windows.calls else 0 end) < call_limit
      and (case when ai_usage_windows.day = excluded.day then ai_usage_windows.reserved_tokens else 0 end) + tokens <= token_limit
      and (case when ai_usage_windows.minute = excluded.minute then ai_usage_windows.minute_calls else 0 end) < 4
    returning true into granted;
    return coalesce(granted, false);
end;
$$;
revoke all on function discovery.reserve_ai_usage(integer, integer, integer) from public;
grant execute on function discovery.reserve_ai_usage(integer, integer, integer) to game_discovery_runtime;
