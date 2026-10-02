begin;

create extension if not exists pgtap with schema extensions;

set local search_path = public, extensions;

select no_plan();

-- Check the database objects and access restrictions.
select has_table(
    'public',
    'recipe_rate_limits',
    'The quota table exists'
);

select has_function(
    'public',
    'consume_recipe_quota',
    array[]::text[],
    'The quota function exists'
);

select ok(
    (
        select relrowsecurity
        from pg_class
        where oid = 'public.recipe_rate_limits'::regclass
    ),
    'Row Level Security is enabled'
);

select ok(
    not has_function_privilege(
        'anon',
        'public.consume_recipe_quota()',
        'EXECUTE'
    ),
    'Anonymous users cannot consume quota'
);

select ok(
    has_function_privilege(
        'authenticated',
        'public.consume_recipe_quota()',
        'EXECUTE'
    ),
    'Authenticated users can consume quota'
);

select ok(
    not has_table_privilege(
        'anon',
        'public.recipe_rate_limits',
        'SELECT,INSERT,UPDATE,DELETE'
    ),
    'Anonymous users cannot access quota records directly'
);

select ok(
    not has_table_privilege(
        'authenticated',
        'public.recipe_rate_limits',
        'SELECT,INSERT,UPDATE,DELETE'
    ),
    'Authenticated users cannot access quota records directly'
);

-- Create fictional users only inside this test transaction.
insert into auth.users (id, email)
values
    (
        'a76c9201-414f-4fe3-a587-75d54709e001',
        'recipe-quota-one@example.test'
    ),
    (
        'a76c9201-414f-4fe3-a587-75d54709e002',
        'recipe-quota-two@example.test'
    );

-- Simulate a request without an authenticated identity.
select set_config('request.jwt.claim.sub', '', true);
select set_config('request.jwt.claims', '{}', true);

select throws_ok(
    'select public.consume_recipe_quota()',
    '42501',
    'Authentication required',
    'An authenticated identity is required'
);

-- Simulate the first user's verified session.
select set_config(
    'request.jwt.claim.sub',
    'a76c9201-414f-4fe3-a587-75d54709e001',
    true
);

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'true',
    'The first request is accepted'
);

select is(
    (
        select minute_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    1,
    'The first request increments the minute counter'
);

select is(
    (
        select day_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    1,
    'The first request increments the daily counter'
);

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'true',
    'The second request is accepted'
);

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'true',
    'The third request is accepted'
);

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'false',
    'The fourth request is rejected'
);

select ok(
    (public.consume_recipe_quota() ->> 'retry_after')::integer
        between 1 and 60,
    'The minute limit returns a valid waiting time'
);

select is(
    (
        select minute_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    3,
    'Rejected requests do not increase the minute counter'
);

select is(
    (
        select day_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    3,
    'Rejected requests do not increase the daily counter'
);

-- A second user has a separate quota.
select set_config(
    'request.jwt.claim.sub',
    'a76c9201-414f-4fe3-a587-75d54709e002',
    true
);

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'true',
    'Another user can generate a recipe independently'
);

select is(
    (
        select day_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    3,
    'Another user does not change the first user quota'
);

select set_config(
    'request.jwt.claim.sub',
    'a76c9201-414f-4fe3-a587-75d54709e001',
    true
);

-- Move the window into the past instead of waiting during tests.
update public.recipe_rate_limits
set minute_started_at = clock_timestamp() - interval '61 seconds'
where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001';

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'true',
    'An expired minute window allows another request'
);

select is(
    (
        select minute_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    1,
    'The new minute window starts with one request'
);

select is(
    (
        select day_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    4,
    'Resetting the minute window preserves the daily usage'
);

-- Prepare the last available daily request.
update public.recipe_rate_limits
set
    minute_started_at = clock_timestamp(),
    minute_count = 0,
    day_count = 19
where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001';

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'true',
    'The twentieth daily request is accepted'
);

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'false',
    'The twenty-first daily request is rejected'
);

select ok(
    (public.consume_recipe_quota() ->> 'retry_after')::integer
        between 1 and 86400,
    'The daily limit returns a valid waiting time'
);

select is(
    (
        select day_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    20,
    'Rejected requests do not increase the exhausted daily counter'
);

select is(
    (
        select minute_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    1,
    'The daily rejection does not consume minute quota'
);

-- Simulate a previous UTC day and an expired minute window.
update public.recipe_rate_limits
set
    day_date = (clock_timestamp() at time zone 'UTC')::date - 1,
    minute_started_at = clock_timestamp() - interval '61 seconds'
where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001';

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'true',
    'A new UTC day allows another request'
);

select is(
    (
        select day_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    1,
    'The new daily counter starts with one request'
);

select is(
    (
        select day_date
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001'
    ),
    (clock_timestamp() at time zone 'UTC')::date,
    'The daily counter uses the current UTC date'
);

-- A new day must not bypass a minute window that is still exhausted.
update public.recipe_rate_limits
set
    day_date = (clock_timestamp() at time zone 'UTC')::date - 1,
    day_count = 20,
    minute_started_at = clock_timestamp(),
    minute_count = 3
where user_id = 'a76c9201-414f-4fe3-a587-75d54709e001';

select is(
    public.consume_recipe_quota() ->> 'allowed',
    'false',
    'A new day does not bypass the active minute limit'
);

-- Execute the function with the actual authenticated database role.
select set_config(
    'request.jwt.claim.sub',
    'a76c9201-414f-4fe3-a587-75d54709e002',
    true
);

set local role authenticated;

select set_config(
    'test.recipe_quota_result',
    public.consume_recipe_quota()::text,
    true
);

reset role;

select is(
    current_setting('test.recipe_quota_result')::jsonb ->> 'allowed',
    'true',
    'The authenticated role can execute the quota function'
);

select is(
    (
        select day_count
        from public.recipe_rate_limits
        where user_id = 'a76c9201-414f-4fe3-a587-75d54709e002'
    ),
    2,
    'The authenticated role consumes its own user quota'
);

select * from finish();

-- Remove all fictional users and counter changes made by this test.
rollback;