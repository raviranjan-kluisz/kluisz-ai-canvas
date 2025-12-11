"""User license assignment API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from kluisz.api.utils import CurrentActiveUser, DbSession
from kluisz.schema.serialize import UUIDstr
from kluisz.services.auth.utils import get_current_active_superuser, get_current_tenant_admin
from kluisz.services.database.models.user.model import User, UserRead
from kluisz.services.license.service import LicenseService

router = APIRouter(prefix="/admin/user-licenses", tags=["User Licenses"])

SuperAdmin = Annotated[User, Depends(get_current_active_superuser)]
TenantAdminOrSuperAdmin = Annotated[User, Depends(get_current_tenant_admin)]


class AssignLicenseRequest(BaseModel):
    user_id: UUIDstr
    tier_id: UUIDstr


class UpgradeLicenseRequest(BaseModel):
    user_id: UUIDstr
    new_tier_id: UUIDstr
    preserve_credits: bool = False


@router.post("/assign", response_model=UserRead)
async def assign_license_to_user(
    request: AssignLicenseRequest,
    current_user: TenantAdminOrSuperAdmin,
    session: DbSession,
) -> User:
    """Assign a license to a user."""
    # Check permissions
    if not current_user.is_platform_superadmin:
        # Tenant admin can only assign to users in their tenant
        target_user = await session.get(User, request.user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        if target_user.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Can only assign licenses to users in your tenant")

    try:
        license_service = LicenseService()
        return await license_service.assign_license_to_user(
            user_id=request.user_id,
            tier_id=request.tier_id,
            assigned_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/unassign/{user_id}", response_model=UserRead)
async def unassign_license_from_user(
    user_id: UUIDstr,
    current_user: TenantAdminOrSuperAdmin,
    session: DbSession,
) -> User:
    """Unassign license from a user."""
    # Check permissions
    if not current_user.is_platform_superadmin:
        target_user = await session.get(User, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        if target_user.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Can only unassign licenses from users in your tenant")

    try:
        license_service = LicenseService()
        return await license_service.unassign_license_from_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/upgrade", response_model=UserRead)
async def upgrade_user_license(
    request: UpgradeLicenseRequest,
    current_user: TenantAdminOrSuperAdmin,
    session: DbSession,
) -> User:
    """Upgrade a user's license to a new tier."""
    # Check permissions
    if not current_user.is_platform_superadmin:
        target_user = await session.get(User, request.user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        if target_user.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Can only upgrade licenses for users in your tenant")

    try:
        license_service = LicenseService()
        return await license_service.upgrade_user_license(
            user_id=request.user_id,
            new_tier_id=request.new_tier_id,
            assigned_by=current_user.id,
            preserve_credits=request.preserve_credits,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

