"""The migration history builds the models' schema and can be rolled back and replayed."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from app.db.base import Base
from tests.conftest import recreate_database, resolve_test_database_url


def _ignore_postgis_tables(obj, name, type_, reflected, compare_to):
    return not (type_ == "table" and reflected and compare_to is None)


def test_migrations_round_trip_and_match_models():
    base = resolve_test_database_url()
    url = base.set(database=f"{base.database}_migrations")
    recreate_database(url)
    engine = create_engine(url)
    config = Config("alembic.ini")
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            command.downgrade(config, "base")
            assert set(inspect(connection).get_table_names()) <= {"alembic_version", "spatial_ref_sys"}
            command.upgrade(config, "head")

        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection, opts={"compare_type": True, "include_object": _ignore_postgis_tables}
            )
            differences = [d for d in compare_metadata(context, Base.metadata) if d[0] != "modify_default"]
            assert differences == []
    finally:
        engine.dispose()
        with create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT").connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
