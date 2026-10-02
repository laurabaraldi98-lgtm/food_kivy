import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4


REQUEST_COUNT = 8


def run_sql(container, sql):
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            container,
            "psql",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input=sql,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    return result.stdout.strip()


def consume_quota(container, user_id, barrier):
    barrier.wait(timeout=30)

    output = run_sql(
        container,
        f"""
        begin;
        set local role authenticated;
        set local "request.jwt.claim.sub" = '{user_id}';

        select public.consume_recipe_quota();

        -- Keep the transaction open briefly so competing requests overlap.
        select pg_sleep(0.2);
        commit;
        """,
    )

    return json.loads(output)


def send_concurrent_requests(container, user_id):
    barrier = Barrier(REQUEST_COUNT)

    with ThreadPoolExecutor(max_workers=REQUEST_COUNT) as executor:
        futures = [
            executor.submit(consume_quota, container, user_id, barrier)
            for _ in range(REQUEST_COUNT)
        ]
        return [future.result() for future in futures]


def check_results(results, expected_allowed):
    allowed = 0

    for result in results:
        if result["allowed"] is True:
            allowed += 1

            if result["retry_after"] != 0:
                raise AssertionError("Accepted request has a waiting time")
        elif result["allowed"] is False:
            if not 1 <= result["retry_after"] <= 86400:
                raise AssertionError("Rejected request has an invalid waiting time")
        else:
            raise AssertionError("Invalid quota response")

    if allowed != expected_allowed:
        raise AssertionError(
            f"Expected {expected_allowed} accepted requests, got {allowed}"
        )


def check_counters(container, user_id, minute_count, day_count):
    output = run_sql(
        container,
        f"""
        select json_build_object(
            'minute_count', minute_count,
            'day_count', day_count
        )
        from public.recipe_rate_limits
        where user_id = '{user_id}';
        """,
    )
    counters = json.loads(output)
    expected = {
        "minute_count": minute_count,
        "day_count": day_count,
    }

    if counters != expected:
        raise AssertionError(
            f"Expected counters {expected}, got {counters}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Test recipe quota concurrency against local Docker Postgres."
    )
    parser.add_argument("--container", required=True)
    args = parser.parse_args()

    user_id = str(uuid4())

    try:
        run_sql(
            args.container,
            f"""
            insert into auth.users (id, email)
            values ('{user_id}', 'quota-{user_id}@example.test');
            """,
        )

        # Start without a quota row to also test concurrent first requests.
        results = send_concurrent_requests(args.container, user_id)
        check_results(results, expected_allowed=3)
        check_counters(args.container, user_id, minute_count=3, day_count=3)
        print("PASS: 8 simultaneous requests accept exactly 3")

        # Leave one daily request available and start a fresh minute window.
        run_sql(
            args.container,
            f"""
            update public.recipe_rate_limits
            set
                minute_started_at = clock_timestamp(),
                minute_count = 0,
                day_date = (clock_timestamp() at time zone 'UTC')::date,
                day_count = 19
            where user_id = '{user_id}';
            """,
        )

        results = send_concurrent_requests(args.container, user_id)
        check_results(results, expected_allowed=1)
        check_counters(args.container, user_id, minute_count=1, day_count=20)
        print("PASS: 8 simultaneous requests cannot exceed the daily limit")

    finally:
        # Deleting the fictional user also removes its quota through ON DELETE CASCADE.
        run_sql(
            args.container,
            f"delete from auth.users where id = '{user_id}';",
        )


if __name__ == "__main__":
    main()