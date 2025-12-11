from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from kluisz.services.database.models.tenant.model import Tenant, TenantUpdate
from kluisz.services.database.models.user.model import User


async def create_tenant(
    session: AsyncSession,
    name: str,
    slug: str,
    max_users: int = 10,
    description: str | None = None,
    is_active: bool = True,
) -> Tenant:
    """Create a new tenant"""
    tenant = Tenant(
        name=name,
        slug=slug,
        max_users=max_users,
        description=description,
        is_active=is_active,
    )
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant


async def get_tenant_by_id(session: AsyncSession, tenant_id: UUID | str) -> Tenant | None:
    """Get tenant by ID"""
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await session.exec(stmt)
    return result.first()


async def get_tenant_by_slug(session: AsyncSession, slug: str) -> Tenant | None:
    """Get tenant by slug"""
    stmt = select(Tenant).where(Tenant.slug == slug)
    result = await session.exec(stmt)
    return result.first()


async def get_all_tenants(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> list[Tenant]:
    """Get all tenants (super admin only)"""
    stmt = select(Tenant)
    if is_active is not None:
        stmt = stmt.where(Tenant.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)
    result = await session.exec(stmt)
    return list(result.all())


async def update_tenant(
    session: AsyncSession,
    tenant: Tenant,
    tenant_update: TenantUpdate,
) -> Tenant:
    """Update tenant"""
    update_data = tenant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    tenant.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(tenant)
    return tenant


async def delete_tenant(session: AsyncSession, tenant_id: UUID | str) -> None:
    """Delete tenant (cascade deletes users, flows, etc.)"""
    tenant = await get_tenant_by_id(session, tenant_id)
    if tenant:
        await session.delete(tenant)
        await session.commit()


async def get_tenant_user_count(session: AsyncSession, tenant_id: UUID | str) -> int:
    """Get number of users in tenant"""
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    stmt = select(func.count(User.id)).where(User.tenant_id == tenant_id)
    result = await session.exec(stmt)
    return result.first() or 0


async def get_tenant_users(
    session: AsyncSession,
    tenant_id: UUID | str,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Get all users in a tenant"""
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    stmt = select(User).where(User.tenant_id == tenant_id).offset(skip).limit(limit)
    result = await session.exec(stmt)
    return list(result.all())
