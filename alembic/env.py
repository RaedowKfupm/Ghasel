"""Alembic environment.

The target database defaults to ``settings.database_url``. Callers such as the
test suite can supply an open connection through ``config.attributes["connection"]``
so migrations run against a different database without touching the dev one.
"""

from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.config import settings
from app.db.base import Base

target_metadata = Base.metadata


def _include_object(obj, name, type_, reflected, compare_to):
    # PostGIS ships its own tables (e.g. spatial_ref_sys); never autogenerate against them.
    return not (type_ == "table" and reflected and compare_to is None)


def _run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=_include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return

    engine = create_engine(settings.database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        _run(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
