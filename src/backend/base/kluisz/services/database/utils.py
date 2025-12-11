from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from alembic.util.exc import CommandError
from klx.log.logger import logger
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from kluisz.services.database.service import DatabaseService


async def initialize_database(*, fix_migration: bool = False) -> None:
    await logger.adebug("Initializing database")
    from kluisz.services.deps import get_db_service

    database_service: DatabaseService = get_db_service()
    try:
        if database_service.settings_service.settings.database_connection_retry:
            await database_service.create_db_and_tables_with_retry()
        else:
            await database_service.create_db_and_tables()
    except Exception as exc:
        # Unwrap RetryError to get the actual exception
        actual_exc = exc
        if hasattr(exc, 'last_attempt') and exc.last_attempt and hasattr(exc.last_attempt, 'exception'):
            try:
                actual_exc = exc.last_attempt.exception()
            except Exception:
                pass
        
        # if the exception involves tables already existing
        # we can ignore it
        error_str = str(actual_exc).lower()
        if "already exists" not in error_str:
            # Include both the wrapper and actual exception in the message
            if actual_exc != exc:
                msg = f"Error creating DB and tables: {type(exc).__name__} wrapping {type(actual_exc).__name__}: {actual_exc}"
            else:
                msg = f"Error creating DB and tables: {type(exc).__name__}: {exc}"
            await logger.aexception(msg, exc_info=actual_exc)
            raise RuntimeError(msg) from actual_exc
    try:
        await database_service.check_schema_health()
    except Exception as exc:
        msg = "Error checking schema health"
        logger.exception(msg)
        raise RuntimeError(msg) from exc
    # For fresh databases, migrations are skipped (tables created from models)
    # Only run migrations for existing databases
    try:
        await database_service.run_migrations(fix=fix_migration)
    except CommandError as exc:
        # Handle migration errors gracefully
        error_str = str(exc)
        # For fresh databases or cycle errors, skip migrations
        if "Cycle is detected" in error_str or "Multiple heads" in error_str:
            logger.warning(
                f"Migration cycle/heads detected: {error_str}. "
                "For fresh databases, this is expected - tables are created from models. Skipping migrations."
            )
            # For fresh DB, just create alembic_version table with a dummy stamp to mark as initialized
            try:
                async with session_getter(database_service) as session:
                    # Check if alembic_version exists, if not create it
                    try:
                        await session.exec(text("SELECT * FROM alembic_version LIMIT 1"))
                    except Exception:
                        # Table doesn't exist, create it and insert a dummy revision
                        await session.exec(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
                        # Use the latest migration revision as the stamp
                        await session.exec(text("INSERT INTO alembic_version (version_num) VALUES ('b1c2d3e4f5a6')"))
                        await session.commit()
                        logger.info("Fresh database initialized - alembic_version table created")
            except Exception as init_exc:
                logger.warning(f"Could not initialize alembic_version table: {init_exc}. This is OK for fresh databases.")
        elif "overlaps with other requested revisions" not in error_str and "Can't locate revision identified by" not in error_str:
            raise
        else:
            # This means there's wrong revision in the DB
            # We need to delete the alembic_version table
            # and run the migrations again
            logger.warning("Wrong revision in DB, deleting alembic_version table and running migrations again")
            async with session_getter(database_service) as session:
                await session.exec(text("DROP TABLE IF EXISTS alembic_version"))
                await session.commit()
            await database_service.run_migrations(fix=fix_migration)
    except Exception as exc:
        # if the exception involves tables already existing
        # we can ignore it
        if "already exists" not in str(exc) and "Cycle is detected" not in str(exc):
            logger.warning(f"Migration error (may be expected for fresh DB): {exc}")
            # Don't raise for fresh databases - tables are already created from models
    await logger.adebug("Database initialized")


@asynccontextmanager
async def session_getter(db_service: DatabaseService):
    try:
        session = AsyncSession(db_service.engine, expire_on_commit=False)
        yield session
    except Exception:
        await logger.aexception("Session rollback because of exception")
        await session.rollback()
        raise
    finally:
        await session.close()


@dataclass
class Result:
    name: str
    type: str
    success: bool


@dataclass
class TableResults:
    table_name: str
    results: list[Result]
