# noqa: INP001
import asyncio
import hashlib
import os
from logging.config import fileConfig
from typing import Any


from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import async_engine_from_config

from klx.log.logger import logger

from kluisz.services.database.service import SQLModel


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata
target_metadata.naming_convention = NAMING_CONVENTION
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Override database URL from environment variable if set
    url = os.getenv("KLUISZ_DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    # Convert relative paths to absolute paths for SQLite
    if url and url.startswith("sqlite") and ":///" in url:
        parts = url.split(":///", 1)
        if len(parts) == 2:
            db_path = parts[1]
            if not os.path.isabs(db_path) and not db_path.startswith(":"):
                from pathlib import Path
                # Find project root by looking for .env or Makefile
                current = Path(__file__).parent
                for _ in range(10):
                    if (current / ".env").exists() or (current / "Makefile").exists():
                        project_root = current
                        break
                    current = current.parent
                else:
                    # Fallback: 5 levels up from alembic/env.py
                    project_root = Path(__file__).parent.parent.parent.parent.parent
                db_path = str(project_root / db_path)
                url = f"{parts[0]}:///{db_path}"
    configure_kwargs = {
        "url": url,
        "target_metadata": target_metadata,
        "literal_binds": True,
        "dialect_opts": {"paramstyle": "named"},
        "render_as_batch": True,
    }

    # Only add prepare_threshold for PostgreSQL
    if url and "postgresql" in url:
        configure_kwargs["prepare_threshold"] = None

    context.configure(**configure_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def _sqlite_do_connect(
    dbapi_connection,
    connection_record,  # noqa: ARG001
):
    # disable pysqlite's emitting of the BEGIN statement entirely.
    # also stops it from emitting COMMIT before any DDL.
    dbapi_connection.isolation_level = None


def _sqlite_do_begin(conn):
    # emit our own BEGIN
    conn.exec_driver_sql("PRAGMA busy_timeout = 60000")
    conn.exec_driver_sql("BEGIN EXCLUSIVE")


def _do_run_migrations(connection):
    configure_kwargs = {
        "connection": connection,
        "target_metadata": target_metadata,
        "render_as_batch": True,
    }

    # Only add prepare_threshold for PostgreSQL
    if connection.dialect.name == "postgresql":
        configure_kwargs["prepare_threshold"] = None

    context.configure(**configure_kwargs)
    with context.begin_transaction():
        if connection.dialect.name == "postgresql":
            # Use namespace from environment variable if provided, otherwise use default static key
            namespace = os.getenv("KLUISZ_MIGRATION_LOCK_NAMESPACE")
            if namespace:
                lock_key = int(hashlib.sha256(namespace.encode()).hexdigest()[:16], 16) % (2**63 - 1)
                logger.info(f"Using migration lock namespace: {namespace}, lock_key: {lock_key}")
            else:
                lock_key = 11223344
                logger.info(f"Using default migration lock_key: {lock_key}")

            connection.execute(text("SET LOCAL lock_timeout = '180s';"))
            connection.execute(text(f"SELECT pg_advisory_xact_lock({lock_key});"))
        context.run_migrations()

async def _run_async_migrations() -> None:
    # Disable prepared statements for PostgreSQL (required for PgBouncer compatibility)
    # SQLite doesn't support this parameter, so only add it for PostgreSQL
    config_section = config.get_section(config.config_ini_section, {})
    
    # Override database URL from environment variable if set
    db_url = os.getenv("KLUISZ_DATABASE_URL") or config_section.get("sqlalchemy.url", "")
    if db_url:
        # Convert relative paths to absolute paths for SQLite
        if db_url.startswith("sqlite") and ":///" in db_url:
            # Extract path from sqlite:///path or sqlite+aiosqlite:///path
            parts = db_url.split(":///", 1)
            if len(parts) == 2:
                db_path = parts[1]
                # If relative path, make it relative to project root
                if not os.path.isabs(db_path) and not db_path.startswith(":"):
                    from pathlib import Path
                    # Find project root by looking for .env or Makefile
                    current = Path(__file__).parent
                    for _ in range(10):
                        if (current / ".env").exists() or (current / "Makefile").exists():
                            project_root = current
                            break
                        current = current.parent
                    else:
                        # Fallback: 5 levels up from alembic/env.py
                        project_root = Path(__file__).parent.parent.parent.parent.parent
                    db_path = str(project_root / db_path)
                    db_url = f"{parts[0]}:///{db_path}"
        config_section["sqlalchemy.url"] = db_url

    connect_args: dict[str, Any] = {}
    if db_url and "postgresql" in db_url:
        connect_args["prepare_threshold"] = None

    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    if connectable.dialect.name == "sqlite":
        # See https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
        listen(connectable.sync_engine, "connect", _sqlite_do_connect)
        listen(connectable.sync_engine, "begin", _sqlite_do_begin)

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(_run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
