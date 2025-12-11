from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.api_key.model import ApiKey
    from kluisz.services.database.models.flow.model import Flow
    from kluisz.services.database.models.folder.model import Folder
    from kluisz.services.database.models.license_tier.model import LicenseTier
    from kluisz.services.database.models.tenant.model import Tenant
    from kluisz.services.database.models.user_usage.model import UserUsageStats
    from kluisz.services.database.models.variable.model import Variable


class UserOptin(BaseModel):
    github_starred: bool = Field(default=False)
    dialog_dismissed: bool = Field(default=False)
    discord_clicked: bool = Field(default=False)
    # Add more opt-in actions as needed


class User(SQLModel, table=True):  # type: ignore[call-arg]
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    username: str = Field(index=True, unique=True)
    password: str = Field()
    profile_image: Optional[str] = Field(default=None, nullable=True)
    is_active: bool = Field(default=False)
    is_platform_superadmin: bool = Field(default=False, description="Platform-level super admin - manages all tenants")
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = Field(default=None, nullable=True)
    
    # Multi-tenant fields
    tenant_id: Optional[UUIDstr] = Field(
        default=None,
        foreign_key="tenant.id",
        index=True,
        nullable=True,
        description="Tenant this user belongs to",
    )
    is_tenant_admin: bool = Field(
        default=False,
        description="Tenant-level admin - can manage users within their tenant",
    )
    
    api_keys: List["ApiKey"] = Relationship(
        sa_relationship=relationship("ApiKey", back_populates="user", cascade="all, delete")
    )
    store_api_key: Optional[str] = Field(default=None, nullable=True)
    flows: List["Flow"] = Relationship(
        sa_relationship=relationship("Flow", back_populates="user")
    )
    variables: List["Variable"] = Relationship(
        sa_relationship=relationship("Variable", back_populates="user", cascade="all, delete")
    )
    folders: List["Folder"] = Relationship(
        sa_relationship=relationship("Folder", back_populates="user", cascade="all, delete")
    )
    optins: Optional[dict[str, Any]] = Field(
        sa_column=Column(JSON, default=lambda: UserOptin().model_dump(), nullable=True)
    )
    
    # License Fields (merged from user_license table)
    license_pool_id: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        index=True,
        description="References tier_id in tenant.license_pools JSON",
    )
    license_tier_id: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        foreign_key="license_tier.id",
        index=True,
        description="License tier assigned to user",
    )
    credits_allocated: int = Field(
        default=0,
        ge=0,
        description="Total credits allocated to user",
    )
    credits_used: int = Field(
        default=0,
        ge=0,
        description="Credits consumed by user",
    )
    credits_per_month: Optional[int] = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Monthly recurring credits (for subscriptions)",
    )
    license_assigned_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="When license was assigned",
    )
    license_assigned_by: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        foreign_key="user.id",
        description="User who assigned the license",
    )
    license_expires_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="License expiration date (None = perpetual)",
    )
    license_is_active: bool = Field(
        default=False,
        index=True,
        description="Whether license is currently active",
    )

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="users")
    # Note: usage_stats relationship removed - analytics now query transaction table directly
    license_tier: Optional["LicenseTier"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[User.license_tier_id]"}
    )


class UserCreate(SQLModel):
    username: str = Field()
    password: str = Field()
    tenant_id: Optional[UUIDstr] = Field(default=None, description="Tenant this user belongs to")
    is_tenant_admin: bool = Field(default=False, description="Whether user is a tenant admin")
    optins: Optional[dict[str, Any]] = Field(
        default={"github_starred": False, "dialog_dismissed": False, "discord_clicked": False}
    )


class UserRead(SQLModel):
    id: UUID = Field(default_factory=uuid4)
    username: str = Field()
    profile_image: Optional[str] = Field()
    store_api_key: Optional[str] = Field(nullable=True)
    is_active: bool = Field()
    is_platform_superadmin: bool = Field(description="Platform-level super admin - manages all tenants")
    tenant_id: Optional[UUIDstr] = Field(nullable=True, description="Tenant this user belongs to")
    is_tenant_admin: bool = Field(description="Whether user is a tenant admin")
    create_at: datetime = Field()
    updated_at: datetime = Field()
    last_login_at: Optional[datetime] = Field(nullable=True)
    optins: Optional[dict[str, Any]] = Field(default=None)
    # License fields
    license_pool_id: Optional[UUIDstr] = Field(default=None, nullable=True)
    license_tier_id: Optional[UUIDstr] = Field(default=None, nullable=True)
    credits_allocated: int = Field(default=0)
    credits_used: int = Field(default=0)
    credits_per_month: Optional[int] = Field(default=None, nullable=True)
    license_assigned_at: Optional[datetime] = Field(default=None, nullable=True)
    license_assigned_by: Optional[UUIDstr] = Field(default=None, nullable=True)
    license_expires_at: Optional[datetime] = Field(default=None, nullable=True)
    license_is_active: bool = Field(default=False)


class UserUpdate(SQLModel):
    username: Optional[str] = None
    profile_image: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_platform_superadmin: Optional[bool] = None
    tenant_id: Optional[UUIDstr] = None
    is_tenant_admin: Optional[bool] = None
    last_login_at: Optional[datetime] = None
    optins: Optional[dict[str, Any]] = None
    # License fields
    license_pool_id: Optional[UUIDstr] = None
    license_tier_id: Optional[UUIDstr] = None
    credits_allocated: Optional[int] = None
    credits_used: Optional[int] = None
    credits_per_month: Optional[int] = None
    license_assigned_at: Optional[datetime] = None
    license_assigned_by: Optional[UUIDstr] = None
    license_expires_at: Optional[datetime] = None
    license_is_active: Optional[bool] = None
