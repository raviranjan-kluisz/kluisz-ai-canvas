"""License pool management API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from kluisz.api.utils import CurrentActiveUser, DbSession
from kluisz.schema.serialize import UUIDstr
from kluisz.services.auth.utils import get_current_active_superuser, get_current_active_user
from kluisz.services.database.models.user.model import User
from kluisz.services.license.service import LicenseService

router = APIRouter(prefix="/admin/license-pools", tags=["License Pools"])

SuperAdmin = Annotated[User, Depends(get_current_active_superuser)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]


class CreatePoolRequest(BaseModel):
    tier_id: UUIDstr
    total_count: int


@router.get("/tenant/{tenant_id}")
async def get_tenant_license_pools(
    tenant_id: UUIDstr,
    current_user: SuperAdmin,
) -> dict:
    """Get all license pools for a tenant (super admin only)."""
    license_service = LicenseService()
    return await license_service.get_tenant_license_pools(tenant_id)


@router.post("/tenant/{tenant_id}")
async def create_or_update_pool(
    tenant_id: UUIDstr,
    pool_data: CreatePoolRequest,
    current_user: SuperAdmin,
) -> dict:
    """Create or update a license pool for a tenant (super admin only)."""
    license_service = LicenseService()
    return await license_service.create_or_update_pool_for_tier(
        tenant_id=tenant_id,
        tier_id=pool_data.tier_id,
        total_count=pool_data.total_count,
        created_by=current_user.id,
    )


@router.get("/my-tenant")
async def get_my_tenant_pools(
    current_user: CurrentUser,
) -> dict:
    """Get license pools for current user's tenant."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    # Check if user is tenant admin or super admin
    if not current_user.is_tenant_admin and not current_user.is_platform_superadmin:
        raise HTTPException(status_code=403, detail="Access denied")

    license_service = LicenseService()
    return await license_service.get_tenant_license_pools(current_user.tenant_id)

