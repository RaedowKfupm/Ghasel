"""Measure the nearby-branch query with and without its GiST index.

Builds a scratch database ("<dev database>_benchmark") from the migrations, seeds
synthetic branches, and runs EXPLAIN (ANALYZE, BUFFERS) on the exact statement the
API executes. The index is dropped inside a transaction that is rolled back, so
both measurements use identical data. The development database is never touched.

    python -m scripts.benchmark_nearby --branches 100000 --runs 15 --radius-km 5
"""

import argparse
import statistics

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection, make_url

from app.core.config import settings
from app.schemas.branch import NearbySearch
from app.services.branches import nearby_branches_query

ORIGIN = {"latitude": 26.3070, "longitude": 50.1460}  # Dhahran

SEED_STATEMENTS = (
    "SELECT setseed(0.42)",  # reproducible synthetic data
    """INSERT INTO "Laundry" (name) VALUES ('Benchmark Laundry')""",
    """
    INSERT INTO "Branches" (laundry_id, branch_name, branch_address, phone, latitude, longitude)
    SELECT (SELECT id FROM "Laundry" LIMIT 1),
           'Branch ' || g, g || ' Benchmark Street', '0500000000',
           16 + random() * 16,  -- roughly the latitude span of Saudi Arabia
           36 + random() * 20   -- and its longitude span
    FROM generate_series(1, :count) AS g
    """,
)


def explain(connection: Connection, sql: str) -> tuple[float, str]:
    rows = connection.execute(text(f"EXPLAIN (ANALYZE, BUFFERS) {sql}")).scalars().all()
    execution_ms = next(float(r.split(":")[1].split()[0]) for r in rows if r.startswith("Execution Time"))
    return execution_ms, "\n".join(rows)


def measure(connection: Connection, sql: str, runs: int) -> tuple[float, str]:
    explain(connection, sql)  # warm the cache so both variants are compared hot
    timings, plan = zip(*(explain(connection, sql) for _ in range(runs)), strict=True)
    return statistics.median(timings), plan[-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branches", type=int, default=100_000)
    parser.add_argument("--runs", type=int, default=15)
    parser.add_argument("--radius-km", type=float, default=5)
    args = parser.parse_args()
    search = NearbySearch(**ORIGIN, radius_km=args.radius_km, limit=20)

    dev_url = make_url(settings.database_url)
    url = dev_url.set(database=f"{dev_url.database}_benchmark".lower())
    admin = create_engine(dev_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{url.database}"'))

    engine = create_engine(url)
    try:
        config = Config("alembic.ini")
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            for statement in SEED_STATEMENTS:
                connection.execute(text(statement), {"count": args.branches})
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text('VACUUM ANALYZE "Branches"'))

        sql = str(
            nearby_branches_query(search).compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
        with engine.connect() as connection:
            matches = connection.execute(text(f"SELECT count(*) FROM ({sql}) AS q")).scalar()
            indexed_ms, indexed_plan = measure(connection, sql, args.runs)
            connection.rollback()

            # DDL is transactional in PostgreSQL: the rollback restores the index.
            connection.execute(text("DROP INDEX ix_branches_location"))
            unindexed_ms, unindexed_plan = measure(connection, sql, args.runs)
            connection.rollback()

        print(f"{args.branches:,} branches, radius {search.radius_km} km, {matches} results, median of {args.runs} runs")
        print(f"\nWITH GiST index: {indexed_ms:.3f} ms\n{indexed_plan}")
        print(f"\nWITHOUT index:   {unindexed_ms:.3f} ms\n{unindexed_plan}")
        print(f"\nSpeed-up: {unindexed_ms / indexed_ms:.1f}x")
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        admin.dispose()


if __name__ == "__main__":
    main()
