-- Store one quota record per user.
create table public.recipe_rate_limits (
    user_id uuid primary key references auth.users(id) on delete cascade,
    minute_started_at timestamptz not null,
    minute_count integer not null default 0
        check (minute_count between 0 and 3),
    day_date date not null,
    day_count integer not null default 0
        check (day_count between 0 and 20)
);

-- Users cannot read or modify counters directly.
alter table public.recipe_rate_limits enable row level security;

revoke all on table public.recipe_rate_limits
from public, anon, authenticated;

-- Consume one request atomically for the authenticated user.
create function public.consume_recipe_quota()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_user_id uuid;
    v_now timestamptz;
    v_today date;
    v_quota public.recipe_rate_limits%rowtype;
    v_retry_after integer := 0;
begin
    -- Read identity from the verified session, never from a client parameter.
    v_user_id := auth.uid();

    if v_user_id is null then
        raise exception 'Authentication required'
            using errcode = '42501';
    end if;

    v_now := clock_timestamp();
    v_today := (v_now at time zone 'UTC')::date;

    insert into public.recipe_rate_limits (
        user_id,
        minute_started_at,
        minute_count,
        day_date,
        day_count
    )
    values (
        v_user_id,
        v_now,
        0,
        v_today,
        0
    )
    on conflict (user_id) do nothing;

    -- Serialize requests belonging to the same user.
    select *
    into strict v_quota
    from public.recipe_rate_limits
    where user_id = v_user_id
    for update;

    -- Refresh the time after waiting for another transaction, if necessary.
    v_now := clock_timestamp();
    v_today := (v_now at time zone 'UTC')::date;

    -- Start a new 60-second window when the previous one has expired.
    if v_now >= v_quota.minute_started_at + interval '60 seconds' then
        v_quota.minute_started_at := v_now;
        v_quota.minute_count := 0;
    end if;

    -- Daily quotas reset at midnight UTC.
    if v_quota.day_date <> v_today then
        v_quota.day_date := v_today;
        v_quota.day_count := 0;
    end if;

    if v_quota.minute_count >= 3 then
        v_retry_after := greatest(
            1,
            ceil(
                extract(
                    epoch from (
                        v_quota.minute_started_at
                        + interval '60 seconds'
                        - v_now
                    )
                )
            )::integer
        );
    end if;

    if v_quota.day_count >= 20 then
        v_retry_after := greatest(
            v_retry_after,
            1,
            ceil(
                extract(
                    epoch from (
                        ((v_today + 1)::timestamp at time zone 'UTC')
                        - v_now
                    )
                )
            )::integer
        );
    end if;

    -- Rejected requests do not consume additional quota.
    if v_retry_after > 0 then
        return jsonb_build_object(
            'allowed', false,
            'retry_after', v_retry_after
        );
    end if;

    update public.recipe_rate_limits
    set
        minute_started_at = v_quota.minute_started_at,
        minute_count = v_quota.minute_count + 1,
        day_date = v_quota.day_date,
        day_count = v_quota.day_count + 1
    where user_id = v_user_id;

    return jsonb_build_object(
        'allowed', true,
        'retry_after', 0
    );
end;
$$;

-- Only authenticated users can consume their own quota.
revoke all on function public.consume_recipe_quota()
from public, anon, authenticated;

grant execute on function public.consume_recipe_quota()
to authenticated;