-- Add reasons to the existing atomic reservation without replacing its boolean API.
-- The old function serializes both granted and denied upserts on the singleton row.
create function discovery.reserve_ai_usage_detailed(tokens integer, call_limit integer, token_limit integer)
returns table(allowed boolean, reason text, retry_at timestamptz)
language plpgsql security definer set search_path = '' as $$
declare
    usage discovery.ai_usage_windows%rowtype;
    utc_day date;
    utc_minute timestamptz;
begin
    if tokens is null or tokens < 1 or tokens > 16000
       or call_limit is null or call_limit < 1 or call_limit > 100
       or token_limit is null or token_limit < 1 or token_limit > 1500000 or tokens > token_limit then
        return query select false, 'invalid_limits'::text, null::timestamptz;
        return;
    end if;
    if discovery.reserve_ai_usage(tokens, call_limit, token_limit) then
        return query select true, 'granted'::text, null::timestamptz;
        return;
    end if;
    select * into usage from discovery.ai_usage_windows where id for update;
    utc_day := (pg_catalog.clock_timestamp() at time zone 'UTC')::date;
    utc_minute := pg_catalog.date_trunc('minute', pg_catalog.clock_timestamp());
    if usage.day = utc_day and usage.calls >= call_limit then
        return query select false, 'daily_calls'::text, ((utc_day + 1)::timestamp at time zone 'UTC');
    elsif usage.day = utc_day and usage.reserved_tokens + tokens > token_limit then
        return query select false, 'daily_units'::text, ((utc_day + 1)::timestamp at time zone 'UTC');
    elsif usage.minute = utc_minute and usage.minute_calls >= 4 then
        return query select false, 'minute_limit'::text, utc_minute + interval '1 minute';
    else
        -- A window boundary or unknown denial must not be called quota exhaustion.
        return query select false, 'accounting_unavailable'::text, null::timestamptz;
    end if;
end;
$$;
revoke all on function discovery.reserve_ai_usage_detailed(integer, integer, integer) from public;
grant execute on function discovery.reserve_ai_usage_detailed(integer, integer, integer) to game_discovery_runtime;
