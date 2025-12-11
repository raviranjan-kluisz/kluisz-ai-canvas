"""Tenant management API endpoints."""

from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from kluisz.services.auth.utils import get_current_active_superuser, get_current_active_user, get_password_hash
from kluisz.services.database.models.tenant.crud import (
    create_tenant,
    delete_tenant,
    get_all_tenants,
    get_tenant_by_id,
    get_tenant_by_slug,
    get_tenant_user_count,
    get_tenant_users,
    update_tenant,
)
from kluisz.services.database.models.tenant.model import Tenant, TenantCreate, TenantRead, TenantUpdate
from kluisz.services.database.models.user.model import User, UserRead
from kluisz.services.database.models.user.crud import get_user_by_id, get_user_by_username
from kluisz.services.database.models.license_tier.model import LicenseTier
from kluisz.services.license.service import LicenseService
from kluisz.initial_setup.setup import get_or_create_default_folder
from kluisz.api.utils import DbSession
from sqlmodel import select


# Request/Response models for tenant user management
class TenantUserCreate(BaseModel):
    """Schema for creating a user within a tenant."""
    username: str
    password: str
    is_tenant_admin: bool = False
    license_tier_id: Optional[str] = None  # Optional license tier to assign during creation


class TenantUserUpdate(BaseModel):
    """Schema for updating a user within a tenant."""
    is_active: Optional[bool] = None
    is_tenant_admin: Optional[bool] = None
    password: Optional[str] = None

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# Type aliases for cleaner signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
SuperAdmin = Annotated[User, Depends(get_current_active_superuser)]


@router.post("/", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint(
    tenant_data: TenantCreate,
    current_user: SuperAdmin,
    session: DbSession,
) -> Tenant:
    """Create a new tenant (super admin only)."""
    # Check if slug already exists
    existing = await get_tenant_by_slug(session, tenant_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant with this slug already exists",
        )

    tenant = await create_tenant(
        session,
        name=tenant_data.name,
        slug=tenant_data.slug,
        max_users=tenant_data.max_users,
        description=tenant_data.description,
        is_active=tenant_data.is_active,
    )
    return tenant


@router.get("/", response_model=list[TenantRead])
async def list_tenants(
    current_user: SuperAdmin,
    session: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    is_active: bool | None = Query(default=None),
) -> list[Tenant]:
    """List all tenants (super admin only)."""
    return await get_all_tenants(session, skip=skip, limit=limit, is_active=is_active)


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> Tenant:
    """Get tenant by ID."""
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access: super admin can access any, others only their own
    if not current_user.is_platform_superadmin and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )

    return tenant


@router.get("/slug/{slug}", response_model=TenantRead)
async def get_tenant_by_slug_endpoint(
    slug: str,
    current_user: CurrentUser,
    session: DbSession,
) -> Tenant:
    """Get tenant by slug."""
    tenant = await get_tenant_by_slug(session, slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access
    if not current_user.is_platform_superadmin and current_user.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )

    return tenant


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant_endpoint(
    tenant_id: UUID,
    tenant_update: TenantUpdate,
    current_user: SuperAdmin,
    session: DbSession,
) -> Tenant:
    """Update tenant (super admin only)."""
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check if slug is being changed and already exists
    if tenant_update.slug and tenant_update.slug != tenant.slug:
        existing = await get_tenant_by_slug(session, tenant_update.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tenant with this slug already exists",
            )

    return await update_tenant(session, tenant, tenant_update)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_endpoint(
    tenant_id: UUID,
    current_user: SuperAdmin,
    session: DbSession,
) -> None:
    """Delete tenant (super admin only). This will cascade delete all tenant data."""
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    await delete_tenant(session, tenant_id)


@router.get("/{tenant_id}/users", response_model=list[UserRead])
async def get_tenant_users_endpoint(
    tenant_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[User]:
    """Get all users in a tenant."""
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access: super admin or tenant admin of this tenant
    if not current_user.is_platform_superadmin:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )
        if not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can view all users",
            )

    return await get_tenant_users(session, tenant_id, skip=skip, limit=limit)


@router.get("/{tenant_id}/users/count")
async def get_tenant_user_count_endpoint(
    tenant_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> dict:
    """Get count of users in a tenant."""
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access
    if not current_user.is_platform_superadmin:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )

    count = await get_tenant_user_count(session, tenant_id)
    return {"tenant_id": str(tenant_id), "user_count": count, "max_users": tenant.max_users}


@router.post("/{tenant_id}/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_tenant_user(
    tenant_id: UUID,
    user_data: TenantUserCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> User:
    """Create a new user within a tenant.
    
    Super admins can create users in any tenant.
    Tenant admins can only create users in their own tenant.
    """
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access: super admin or tenant admin of this tenant
    if not current_user.is_platform_superadmin:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )
        if not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can create users",
            )

    # Check tenant is active
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add users to inactive tenant",
        )

    # Check user limit based on subscription or tenant default
    user_count = await get_tenant_user_count(session, tenant_id)
    
    # Get max_users from subscription tier or tenant default
    max_users = tenant.max_users
    if tenant.subscription_tier_id:
        stmt = select(LicenseTier).where(LicenseTier.id == tenant.subscription_tier_id)
        result = await session.execute(stmt)
        tier = result.scalars().first()
        if tier and tier.max_users:
            max_users = tier.max_users
    
    if user_count >= max_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant has reached maximum user limit ({max_users})",
        )

    # Check if username already exists
    existing_user = await get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is unavailable",
        )

    # Create user
    try:
        new_user = User(
            username=user_data.username,
            password=get_password_hash(user_data.password),
            tenant_id=tenant_id,
            is_tenant_admin=user_data.is_tenant_admin,
            is_active=True,  # Users created by admin are active by default
            is_platform_superadmin=False,
        )
        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)
        
        # Assign license if license_tier_id is provided
        if user_data.license_tier_id:
            try:
                # Assign license within the same transaction
                license_service = LicenseService()
                tier_id_uuid = UUID(user_data.license_tier_id)
                
                # Get tenant and tier
                tenant = await session.get(Tenant, tenant_id)
                if not tenant:
                    raise HTTPException(status_code=404, detail="Tenant not found")
                
                tier = await session.get(LicenseTier, tier_id_uuid)
                if not tier:
                    raise HTTPException(status_code=404, detail="License tier not found")
                
                # Check if pool exists and has available licenses
                pools = tenant.license_pools or {}
                tier_id_str = str(tier_id_uuid)
                
                if tier_id_str not in pools:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No license pool found for tier {tier.name}"
                    )
                
                pool = pools[tier_id_str]
                available = pool.get("available_count", 0)
                
                if available <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No available licenses in {tier.name} pool"
                    )
                
                # Update pool
                pool["available_count"] = available - 1
                pool["assigned_count"] = pool.get("assigned_count", 0) + 1
                pool["updated_at"] = datetime.now(timezone.utc).isoformat()
                tenant.license_pools = pools
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(tenant, "license_pools")
                
                # Assign license to user
                new_user.license_tier_id = tier_id_uuid
                new_user.credits_allocated = tier.default_credits or 0
                new_user.credits_used = 0
                new_user.credits_per_month = tier.default_credits_per_month
                new_user.license_is_active = True
                new_user.license_assigned_at = datetime.now(timezone.utc)
                new_user.license_assigned_by = current_user.id
                
                session.add(tenant)
                session.add(new_user)
                
            except HTTPException:
                raise
            except Exception as e:
                # If license assignment fails, rollback user creation
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to assign license: {str(e)}"
                ) from e
        
        # Create default folder for the user
        folder = await get_or_create_default_folder(session, new_user.id)
        if not folder:
            raise HTTPException(status_code=500, detail="Error creating default project")
            
        await session.commit()
        return new_user
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Error creating user") from e


@router.patch("/{tenant_id}/users/{user_id}", response_model=UserRead)
async def update_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    user_update: TenantUserUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> User:
    """Update a user within a tenant.
    
    Super admins can update users in any tenant.
    Tenant admins can only update users in their own tenant.
    """
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access
    if not current_user.is_platform_superadmin:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )
        if not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can update users",
            )

    # Get the user
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user belongs to this tenant
    if user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to this tenant",
        )

    # Prevent non-super-admins from modifying super admins
    if user.is_platform_superadmin and not current_user.is_platform_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify super admin users",
        )

    # Apply updates
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.is_tenant_admin is not None:
        user.is_tenant_admin = user_update.is_tenant_admin
    if user_update.password:
        user.password = get_password_hash(user_update.password)

    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{tenant_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> None:
    """Remove a user from a tenant.
    
    Super admins can delete users from any tenant.
    Tenant admins can only delete users from their own tenant.
    """
    tenant = await get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check access
    if not current_user.is_platform_superadmin:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )
        if not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can delete users",
            )

    # Get the user
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user belongs to this tenant
    if user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to this tenant",
        )

    # Prevent deleting super admins
    if user.is_platform_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete super admin users",
        )

    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    await session.delete(user)
    await session.commit()

