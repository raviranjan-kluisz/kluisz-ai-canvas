"""License management API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from kluisz.services.auth.utils import get_current_active_superuser, get_current_active_user
from kluisz.services.database.models.license.crud import (
    create_license,
    create_license_from_tier_helper,
    delete_license,
    get_active_license_for_tenant,
    get_all_licenses,
    get_license_by_id,
    update_license,
)
from kluisz.services.database.models.license.model import (
    License,
    LicenseCreate,
    LicenseRead,
    LicenseTier,
    LicenseUpdate,
)
from kluisz.services.database.models.tenant.crud import get_tenant_by_id
from kluisz.services.database.models.user.model import User
from kluisz.api.utils import DbSession

router = APIRouter(prefix="/licenses", tags=["Licenses"])


# Type aliases
CurrentUser = Annotated[User, Depends(get_current_active_user)]
SuperAdmin = Annotated[User, Depends(get_current_active_superuser)]


@router.post("/", response_model=LicenseRead, status_code=status.HTTP_201_CREATED)
async def create_license_endpoint(
    license_data: LicenseCreate,
    current_user: SuperAdmin,
    session: DbSession,
) -> License:
    """Create a new license (super admin only)."""
    # Verify tenant exists
    tenant = await get_tenant_by_id(session, license_data.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    license_obj = await create_license(session, license_data)
    return license_obj


@router.post("/from-tier", response_model=LicenseRead, status_code=status.HTTP_201_CREATED)
async def create_license_from_tier(
    current_user: SuperAdmin,
    session: DbSession,
    tenant_id: UUID = Query(..., description="Tenant ID to assign license to"),
    tier: LicenseTier = Query(..., description="License tier"),
) -> License:
    """Create license from tier configuration (super admin only)."""
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    license_obj = await create_license_from_tier_helper(session, tenant_id, tier)
    return license_obj


@router.get("/", response_model=list[LicenseRead])
async def list_licenses(
    current_user: SuperAdmin,
    session: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_id: UUID | None = Query(default=None),
) -> list[License]:
    """List all licenses (super admin only)."""
    return await get_all_licenses(session, skip=skip, limit=limit, tenant_id=tenant_id)


@router.get("/{license_id}", response_model=LicenseRead)
async def get_license(
    license_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> License:
    """Get license by ID."""
    license_obj = await get_license_by_id(session, license_id)
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    # Check access
    if not current_user.is_platform_superadmin and current_user.tenant_id != license_obj.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this license",
        )

    return license_obj


@router.get("/tenant/{tenant_id}/active")
async def get_active_license(
    tenant_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> dict:
    """Get active license/subscription info for a tenant.
    
    Note: The License model is disabled. This endpoint returns subscription info from the tenant.
    """
    from kluisz.services.database.models.tenant.model import Tenant
    from kluisz.services.database.models.license_tier.model import LicenseTier
    
    # Check access
    if not current_user.is_platform_superadmin and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )

    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Return subscription info from tenant
    subscription_info = {
        "tenant_id": str(tenant_id),
        "subscription_tier_id": str(tenant.subscription_tier_id) if tenant.subscription_tier_id else None,
        "subscription_status": tenant.subscription_status,
        "subscription_license_count": tenant.subscription_license_count or 0,
        "subscription_start_date": tenant.subscription_start_date.isoformat() if tenant.subscription_start_date else None,
        "subscription_end_date": tenant.subscription_end_date.isoformat() if tenant.subscription_end_date else None,
        "subscription_renewal_date": tenant.subscription_renewal_date.isoformat() if tenant.subscription_renewal_date else None,
        "subscription_amount": float(tenant.subscription_amount) if tenant.subscription_amount else None,
        "subscription_currency": tenant.subscription_currency or "USD",
    }
    
    # Get tier info if available
    if tenant.subscription_tier_id:
        tier = await session.get(LicenseTier, tenant.subscription_tier_id)
        if tier:
            subscription_info["tier"] = {
                "id": str(tier.id),
                "name": tier.name,
                "default_credits": tier.default_credits,
                "credits_per_usd": float(tier.credits_per_usd) if tier.credits_per_usd else None,
            }
    
    return subscription_info


@router.patch("/{license_id}", response_model=LicenseRead)
async def update_license_endpoint(
    license_id: UUID,
    license_update: LicenseUpdate,
    current_user: SuperAdmin,
    session: DbSession,
) -> License:
    """Update license (super admin only)."""
    license_obj = await get_license_by_id(session, license_id)
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    return await update_license(session, license_obj, license_update)


@router.delete("/{license_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_license_endpoint(
    license_id: UUID,
    current_user: SuperAdmin,
    session: DbSession,
) -> None:
    """Delete license (super admin only)."""
    license_obj = await get_license_by_id(session, license_id)
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    await delete_license(session, license_id)


@router.get("/tiers/info")
async def get_tier_info(
    current_user: CurrentUser,
) -> dict:
    """Get information about available license tiers."""
    from kluisz.services.database.models.license.tier_config import TIER_CONFIGS

    return {
        "tiers": [
            {
                "tier": tier.value,
                "max_users": config["max_users"],
                "max_flows": config["max_flows"],
                "max_api_calls": config["max_api_calls"],
                "credits": config["credits"],
                "credits_per_month": config["credits_per_month"],
                "price": str(config["price"]),
                "features": config["features"],
            }
            for tier, config in TIER_CONFIGS.items()
        ]
    }

