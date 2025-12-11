"""License tier management API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from kluisz.api.utils import CurrentActiveUser, DbSession
from kluisz.schema.serialize import UUIDstr
from kluisz.services.auth.utils import get_current_active_superuser, get_current_tenant_admin
from kluisz.services.database.models.license_tier.model import (
    LicenseTier,
    LicenseTierCreate,
    LicenseTierRead,
    LicenseTierUpdate,
)
from kluisz.services.database.models.user.model import User

router = APIRouter(prefix="/admin/license-tiers", tags=["License Tiers"])

SuperAdmin = Annotated[User, Depends(get_current_active_superuser)]
TenantAdminOrSuperAdmin = Annotated[User, Depends(get_current_tenant_admin)]


@router.get("/", response_model=list[LicenseTierRead])
async def list_license_tiers(
    current_user: TenantAdminOrSuperAdmin,  # Both tenant admin and super admin can list tiers
    session: DbSession,
) -> list[LicenseTier]:
    """List all license tiers (tenant admin or super admin)."""
    stmt = select(LicenseTier).order_by(LicenseTier.name)
    result = await session.exec(stmt)
    return list(result.all())


@router.get("/{tier_id}", response_model=LicenseTierRead)
async def get_license_tier(
    tier_id: UUIDstr,
    current_user: SuperAdmin,
    session: DbSession,
) -> LicenseTier:
    """Get license tier by ID (super admin only)."""
    tier = await session.get(LicenseTier, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="License tier not found")
    return tier


@router.post("/", response_model=LicenseTierRead, status_code=status.HTTP_201_CREATED)
async def create_license_tier(
    tier_data: LicenseTierCreate,
    current_user: SuperAdmin,
    session: DbSession,
) -> LicenseTier:
    """Create a new license tier (super admin only)."""
    # Check if tier with same name exists
    stmt = select(LicenseTier).where(LicenseTier.name == tier_data.name)
    existing = await session.exec(stmt)
    if existing.first():
        raise HTTPException(status_code=400, detail="License tier with this name already exists")

    tier = LicenseTier(
        **tier_data.model_dump(),
        created_by=current_user.id,
    )
    session.add(tier)
    await session.commit()
    await session.refresh(tier)
    return tier


@router.put("/{tier_id}", response_model=LicenseTierRead)
async def update_license_tier(
    tier_id: UUIDstr,
    tier_data: LicenseTierUpdate,
    current_user: SuperAdmin,
    session: DbSession,
) -> LicenseTier:
    """Update a license tier (super admin only)."""
    tier = await session.get(LicenseTier, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="License tier not found")

    # Check name uniqueness if name is being updated
    if tier_data.name and tier_data.name != tier.name:
        stmt = select(LicenseTier).where(LicenseTier.name == tier_data.name)
        existing = await session.exec(stmt)
        if existing.first():
            raise HTTPException(status_code=400, detail="License tier with this name already exists")

    update_data = tier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tier, field, value)

    tier.updated_at = tier.updated_at  # Trigger update
    session.add(tier)
    await session.commit()
    await session.refresh(tier)
    return tier


@router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_license_tier(
    tier_id: UUIDstr,
    current_user: SuperAdmin,
    session: DbSession,
) -> None:
    """Delete a license tier (super admin only)."""
    tier = await session.get(LicenseTier, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="License tier not found")

    # Check if tier is used in any tenant pools
    from kluisz.services.database.models.tenant.model import Tenant

    stmt = select(Tenant).where(Tenant.license_pools.isnot(None))
    result = await session.exec(stmt)
    tenants = result.all()

    for tenant in tenants:
        pools = tenant.license_pools or {}
        if str(tier_id) in pools:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete tier: used in tenant {tenant.id} pools",
            )

    await session.delete(tier)
    await session.commit()

