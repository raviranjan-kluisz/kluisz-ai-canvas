from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from klx.log.logger import logger
from klx.services.settings.constants import DEFAULT_SUPERADMIN, DEFAULT_SUPERADMIN_PASSWORD
from sqlalchemy import delete
from sqlalchemy import exc as sqlalchemy_exc
from sqlmodel import col, select

from kluisz.services.auth.utils import create_super_user, verify_password
from kluisz.services.cache.base import ExternalAsyncBaseCacheService
from kluisz.services.cache.factory import CacheServiceFactory
from kluisz.services.database.models.transactions.model import TransactionTable
from kluisz.services.database.models.vertex_builds.model import VertexBuildTable
from kluisz.services.database.utils import initialize_database
from kluisz.services.schema import ServiceType

from .deps import get_db_service, get_service, get_settings_service, session_scope


async def seed_feature_registry_if_needed(session) -> None:
    """Seed the feature registry with default features if the table exists."""
    try:
        from kluisz.initial_setup.seed_features import seed_default_model_registry, seed_feature_registry

        # Try to seed features - will work if tables exist
        await seed_feature_registry(session)
        await seed_default_model_registry(session)
        await logger.adebug("Feature registry seeded successfully")
    except Exception as e:
        # Tables may not exist yet - that's fine, migrations will create them
        await logger.adebug(f"Could not seed feature registry (tables may not exist yet): {e}")

if TYPE_CHECKING:
    from klx.services.settings.manager import SettingsService
    from sqlmodel.ext.asyncio.session import AsyncSession


async def get_or_create_super_user(session: AsyncSession, username, password, is_default):
    from kluisz.services.database.models.user.model import User

    stmt = select(User).where(User.username == username)
    result = await session.exec(stmt)
    user = result.first()

    if user and user.is_platform_superadmin:
        return None  # Super admin already exists

    if user and is_default:
        if user.is_platform_superadmin:
            if verify_password(password, user.password):
                return None
            # Super admin exists but password is incorrect
            # which means that the user has changed the
            # base super admin credentials.
            # This means that the user has already created
            # a super admin and changed the password in the UI
            # so we don't need to do anything.
            await logger.adebug(
                "Super admin exists but password is incorrect. "
                "This means that the user has changed the "
                "base super admin credentials."
            )
            return None
        logger.debug("User with super admin credentials exists but is not a super admin.")
        return None

    if user:
        if verify_password(password, user.password):
            msg = "User with super admin credentials exists but is not a super admin."
            raise ValueError(msg)
        msg = "Incorrect super admin credentials"
        raise ValueError(msg)

    if is_default:
        logger.debug("Creating default super admin.")
    else:
        logger.debug("Creating super admin.")
    return await create_super_user(username, password, db=session)


async def setup_superadmin(settings_service: SettingsService, session: AsyncSession) -> None:
    if settings_service.auth_settings.AUTO_LOGIN:
        await logger.adebug("AUTO_LOGIN is set to True. Creating default super admin.")
        username = DEFAULT_SUPERADMIN
        password = DEFAULT_SUPERADMIN_PASSWORD.get_secret_value()
    else:
        # Remove the default super admin if it exists
        await teardown_superadmin(settings_service, session)
        # If AUTO_LOGIN is disabled, attempt to use configured credentials
        # or fall back to default credentials if none are provided.
        username = settings_service.auth_settings.SUPERADMIN or DEFAULT_SUPERADMIN
        password = (settings_service.auth_settings.SUPERADMIN_PASSWORD or DEFAULT_SUPERADMIN_PASSWORD).get_secret_value()

    if not username or not password:
        msg = "Username and password must be set"
        raise ValueError(msg)

    is_default = (username == DEFAULT_SUPERADMIN) and (password == DEFAULT_SUPERADMIN_PASSWORD.get_secret_value())

    try:
        user = await get_or_create_super_user(
            session=session, username=username, password=password, is_default=is_default
        )
        if user is not None:
            await logger.adebug("Super admin created successfully.")
            # Initialize environment variables as global variables for the new super admin
            await _initialize_superadmin_variables(user.id, session)
        else:
            # User already exists - still initialize variables in case new env vars were added
            from kluisz.services.database.models.user.model import User

            stmt = select(User).where(User.username == username)
            result = await session.exec(stmt)
            existing_user = result.first()
            if existing_user:
                await _initialize_superadmin_variables(existing_user.id, session)
    except Exception as exc:
        logger.exception(exc)
        msg = "Could not create super admin. Please create a super admin manually."
        raise RuntimeError(msg) from exc
    finally:
        # Scrub credentials from in-memory settings after setup
        settings_service.auth_settings.reset_credentials()


async def _initialize_superadmin_variables(user_id, session: AsyncSession) -> None:
    """Initialize environment variables as global variables for the superadmin."""
    try:
        from kluisz.services.deps import get_variable_service

        await get_variable_service().initialize_user_variables(user_id, session)
        await logger.adebug("Environment variables initialized for superadmin.")
        
        # Initialize agentic variables if agentic experience is enabled
        if get_settings_service().settings.agentic_experience:
            from kluisz.api.utils.mcp.agentic_mcp import initialize_agentic_user_variables

            await initialize_agentic_user_variables(user_id, session)
            await logger.adebug("Agentic variables initialized for superadmin.")
    except Exception as e:
        # Don't fail setup if variable initialization fails
        await logger.awarning(f"Could not initialize environment variables for superadmin: {e}")


async def teardown_superadmin(settings_service, session: AsyncSession) -> None:
    """Teardown the super admin."""
    # If AUTO_LOGIN is True, we will remove the default super admin
    # from the database.

    if not settings_service.auth_settings.AUTO_LOGIN:
        try:
            await logger.adebug("AUTO_LOGIN is set to False. Removing default super admin if exists.")
            username = DEFAULT_SUPERADMIN
            from kluisz.services.database.models.user.model import User

            stmt = select(User).where(User.username == username)
            result = await session.exec(stmt)
            user = result.first()
            # Check if super admin was ever logged in, if not delete it
            # if it has logged in, it means the user is using it to login
            if user and user.is_platform_superadmin is True and not user.last_login_at:
                await session.delete(user)
                await session.commit()
                await logger.adebug("Default super admin removed successfully.")

        except Exception as exc:
            # Don't fail startup if we can't remove super admin
            # This might happen if the user doesn't exist or has dependencies
            error_str = str(exc).lower()
            if "does not exist" in error_str or "not found" in error_str:
                await logger.adebug(f"Super admin does not exist, nothing to remove: {exc}")
            else:
                await logger.awarning(f"Could not remove default super admin (non-critical): {exc}")
                # Don't raise - this is not critical for startup


async def teardown_services() -> None:
    """Teardown all the services."""
    import sys
    import traceback
    
    try:
        async with session_scope() as session:
            await teardown_superadmin(get_settings_service(), session)
    except RecursionError:
        await logger.aerror("RecursionError during teardown_superadmin. Stack trace:")
        await logger.aerror("".join(traceback.format_stack()[:50]))
    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Error during teardown_superadmin: {e}")

    try:
        from klx.services.manager import get_service_manager

        service_manager = get_service_manager()
        await service_manager.teardown()
    except RecursionError:
        await logger.aerror("RecursionError during service_manager.teardown. Stack trace:")
        await logger.aerror("".join(traceback.format_stack()[:50]))
    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Error during service_manager.teardown: {e}")


def initialize_settings_service() -> None:
    """Initialize the settings manager."""
    from klx.services.settings import factory as settings_factory

    get_service(ServiceType.SETTINGS_SERVICE, settings_factory.SettingsServiceFactory())


def initialize_session_service() -> None:
    """Initialize the session manager."""
    from kluisz.services.cache import factory as cache_factory
    from kluisz.services.session import factory as session_service_factory

    initialize_settings_service()

    get_service(
        ServiceType.CACHE_SERVICE,
        cache_factory.CacheServiceFactory(),
    )

    get_service(
        ServiceType.SESSION_SERVICE,
        session_service_factory.SessionServiceFactory(),
    )


async def clean_transactions(settings_service: SettingsService, session: AsyncSession) -> None:
    """Clean up old transactions from the database.

    This function deletes transactions that exceed the maximum number to keep (configured in settings).
    It orders transactions by timestamp descending and removes the oldest ones beyond the limit.

    Args:
        settings_service: The settings service containing configuration like max_transactions_to_keep
        session: The database session to use for the deletion
    """
    try:
        # Delete transactions using bulk delete
        delete_stmt = delete(TransactionTable).where(
            col(TransactionTable.id).in_(
                select(TransactionTable.id)
                .order_by(col(TransactionTable.timestamp).desc())
                .offset(settings_service.settings.max_transactions_to_keep)
            )
        )

        await session.exec(delete_stmt)
        logger.debug("Successfully cleaned up old transactions")
    except (sqlalchemy_exc.SQLAlchemyError, asyncio.TimeoutError) as exc:
        logger.error(f"Error cleaning up transactions: {exc!s}")
        # Don't re-raise since this is a cleanup task


async def clean_vertex_builds(settings_service: SettingsService, session: AsyncSession) -> None:
    """Clean up old vertex builds from the database.

    This function deletes vertex builds that exceed the maximum number to keep (configured in settings).
    It orders vertex builds by timestamp descending and removes the oldest ones beyond the limit.

    Args:
        settings_service: The settings service containing configuration like max_vertex_builds_to_keep
        session: The database session to use for the deletion
    """
    try:
        # Delete vertex builds using bulk delete
        delete_stmt = delete(VertexBuildTable).where(
            col(VertexBuildTable.id).in_(
                select(VertexBuildTable.id)
                .order_by(col(VertexBuildTable.timestamp).desc())
                .offset(settings_service.settings.max_vertex_builds_to_keep)
            )
        )

        await session.exec(delete_stmt)
        logger.debug("Successfully cleaned up old vertex builds")
    except (sqlalchemy_exc.SQLAlchemyError, asyncio.TimeoutError) as exc:
        logger.error(f"Error cleaning up vertex builds: {exc!s}")
        # Don't re-raise since this is a cleanup task


def register_all_service_factories() -> None:
    """Register all available service factories with the service manager."""
    # Import all service factories
    from klx.services.manager import get_service_manager

    service_manager = get_service_manager()
    from klx.services.mcp_composer import factory as mcp_composer_factory
    from klx.services.settings import factory as settings_factory

    from kluisz.services.auth import factory as auth_factory
    from kluisz.services.cache import factory as cache_factory
    from kluisz.services.chat import factory as chat_factory
    from kluisz.services.database import factory as database_factory
    from kluisz.services.job_queue import factory as job_queue_factory
    from kluisz.services.session import factory as session_factory
    from kluisz.services.shared_component_cache import factory as shared_component_cache_factory
    from kluisz.services.state import factory as state_factory
    from kluisz.services.storage import factory as storage_factory
    from kluisz.services.store import factory as store_factory
    from kluisz.services.task import factory as task_factory
    from kluisz.services.telemetry import factory as telemetry_factory
    from kluisz.services.tracing import factory as tracing_factory
    from kluisz.services.variable import factory as variable_factory

    # Register all factories
    service_manager.register_factory(settings_factory.SettingsServiceFactory())
    service_manager.register_factory(cache_factory.CacheServiceFactory())
    service_manager.register_factory(chat_factory.ChatServiceFactory())
    service_manager.register_factory(database_factory.DatabaseServiceFactory())
    service_manager.register_factory(session_factory.SessionServiceFactory())
    service_manager.register_factory(storage_factory.StorageServiceFactory())
    service_manager.register_factory(variable_factory.VariableServiceFactory())
    service_manager.register_factory(telemetry_factory.TelemetryServiceFactory())
    service_manager.register_factory(tracing_factory.TracingServiceFactory())
    service_manager.register_factory(state_factory.StateServiceFactory())
    service_manager.register_factory(job_queue_factory.JobQueueServiceFactory())
    service_manager.register_factory(task_factory.TaskServiceFactory())
    service_manager.register_factory(store_factory.StoreServiceFactory())
    service_manager.register_factory(shared_component_cache_factory.SharedComponentCacheServiceFactory())
    service_manager.register_factory(auth_factory.AuthServiceFactory())
    service_manager.register_factory(mcp_composer_factory.MCPComposerServiceFactory())
    service_manager.set_factory_registered()


async def initialize_services(*, fix_migration: bool = False) -> None:
    """Initialize all the services needed."""
    # Register all service factories first
    register_all_service_factories()

    cache_service = get_service(ServiceType.CACHE_SERVICE, default=CacheServiceFactory())
    # Test external cache connection
    if isinstance(cache_service, ExternalAsyncBaseCacheService) and not (await cache_service.is_connected()):
        msg = "Cache service failed to connect to external database"
        raise ConnectionError(msg)

    # Setup the super admin
    await initialize_database(fix_migration=fix_migration)
    db_service = get_db_service()
    await db_service.initialize_alembic_log_file()
    async with session_scope() as session:
        settings_service = get_service(ServiceType.SETTINGS_SERVICE)
        await setup_superadmin(settings_service, session)
    try:
        await get_db_service().assign_orphaned_flows_to_superadmin()
    except sqlalchemy_exc.IntegrityError as exc:
        await logger.awarning(f"Error assigning orphaned flows to the super admin: {exc!s}")

    async with session_scope() as session:
        await clean_transactions(settings_service, session)
        await clean_vertex_builds(settings_service, session)
    
    # Seed feature registry (runs regardless of AUTO_LOGIN setting)
    async with session_scope() as session:
        await seed_feature_registry_if_needed(session)
