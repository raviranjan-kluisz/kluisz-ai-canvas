from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from kluisz.services.database.models.license.model import License, LicenseCreate, LicenseTier, LicenseUpdate
from kluisz.services.database.models.license.tier_config import create_license_from_tier


async def create_license(
    session: AsyncSession,
    license_data: LicenseCreate,
) -> License:
    """Create a new license"""
    license = License(**license_data.model_dump())
    session.add(license)
    await session.commit()
    await session.refresh(license)
    return license


async def get_license_by_id(session: AsyncSession, license_id: UUID | str) -> License | None:
    """Get license by ID"""
    if isinstance(license_id, str):
        license_id = UUID(license_id)
    stmt = select(License).where(License.id == license_id)
    result = await session.exec(stmt)
    return result.first()


async def get_all_licenses(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    tenant_id: UUID | str | None = None,
) -> list[License]:
    """Get all licenses, optionally filtered by tenant"""
    stmt = select(License)
    if tenant_id is not None:
        if isinstance(tenant_id, str):
            tenant_id = UUID(tenant_id)
        stmt = stmt.where(License.tenant_id == tenant_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await session.exec(stmt)
    return list(result.all())


async def get_active_license_for_tenant(
    session: AsyncSession,
    tenant_id: UUID | str,
) -> License | None:
    """Get active license for tenant"""
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    stmt = (
        select(License)
        .where(License.tenant_id == tenant_id)
        .where(License.is_active == True)  # noqa: E712
        .order_by(License.created_at.desc())
    )
    result = await session.exec(stmt)
    return result.first()


async def create_license_from_tier_helper(
    session: AsyncSession,
    tenant_id: UUID | str,
    tier: LicenseTier,
) -> License:
    """Create license from tier configuration"""
    if isinstance(tenant_id, str):
        tenant_id = str(tenant_id)
    else:
        tenant_id = str(tenant_id)

    config = create_license_from_tier(tenant_id, tier)
    license = License(**config)
    session.add(license)
    await session.commit()
    await session.refresh(license)
    return license


async def update_license(
    session: AsyncSession,
    license: License,
    license_update: LicenseUpdate,
) -> License:
    """Update license"""
    update_data = license_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(license, field, value)
    license.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(license)
    return license


async def delete_license(session: AsyncSession, license_id: UUID | str) -> None:
    """Delete license"""
    license = await get_license_by_id(session, license_id)
    if license:
        await session.delete(license)
        await session.commit()
