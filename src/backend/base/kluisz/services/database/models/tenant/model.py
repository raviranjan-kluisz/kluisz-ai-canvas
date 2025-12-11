from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, List
from uuid import uuid4

from sqlalchemy import JSON, Numeric
from sqlalchemy import Column as SAColumn
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.api_key.model import ApiKey
    from kluisz.services.database.models.file.model import File
    from kluisz.services.database.models.flow.model import Flow
    from kluisz.services.database.models.folder.model import Folder
    from kluisz.services.database.models.license_tier.model import LicenseTier
    from kluisz.services.database.models.subscription.model import Subscription
    from kluisz.services.database.models.user.model import User
    from kluisz.services.database.models.user_usage.model import UserUsageStats
    from kluisz.services.database.models.variable.model import Variable
    from kluisz.services.database.models.tenant_usage.model import TenantUsageStats


class TenantBase(SQLModel):
    """Base tenant model with common fields"""

    name: str = Field(index=True, description="Tenant name")
    slug: str = Field(index=True, unique=True, description="URL-friendly tenant identifier")
    is_active: bool = Field(default=True, index=True, description="Whether tenant is active")
    max_users: int = Field(
        default=10,
        description="Maximum number of users allowed for this tenant (from license)",
    )
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Optional tenant description",
    )


class Tenant(TenantBase, table=True):  # type: ignore[call-arg]
    """Tenant database model"""

    __tablename__ = "tenant"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Tenant creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # License Pools (merged from license_pool table)
    # JSON structure: {tier_id: {total_count, available_count, assigned_count, created_by, created_at, updated_at}}
    license_pools: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSON),
        description="License pools by tier_id stored as JSON",
    )

    # Subscription Fields (for monthly subscriptions)
    subscription_tier_id: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        foreign_key="license_tier.id",
        index=True,
        description="Current subscription tier",
    )
    subscription_license_count: int = Field(
        default=0,
        ge=0,
        description="Number of licenses in subscription",
    )
    subscription_status: Optional[str] = Field(
        default=None,
        nullable=True,
        index=True,
        description="Subscription status: active, cancelled, past_due, trialing, expired",
    )
    subscription_start_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Subscription start date",
    )
    subscription_end_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Subscription end date",
    )
    subscription_renewal_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        index=True,
        description="Next subscription renewal date",
    )
    subscription_payment_method_id: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Stripe payment method ID",
    )
    subscription_amount: Optional[Decimal] = Field(
        default=None,
        sa_column=SAColumn(Numeric(10, 2), nullable=True),
        description="Monthly subscription amount",
    )
    subscription_currency: str = Field(
        default="USD",
        description="Subscription currency",
    )

    # Relationships
    users: List["User"] = Relationship(
        sa_relationship=relationship("User", back_populates="tenant")
    )
    subscriptions: List["Subscription"] = Relationship(
        sa_relationship=relationship("Subscription", back_populates="tenant")
    )
    # Note: usage_stats and user_usage_stats relationships removed - analytics now query transaction table directly
    flows: List["Flow"] = Relationship(
        sa_relationship=relationship("Flow", back_populates="tenant")
    )
    folders: List["Folder"] = Relationship(
        sa_relationship=relationship("Folder", back_populates="tenant")
    )
    variables: List["Variable"] = Relationship(
        sa_relationship=relationship("Variable", back_populates="tenant")
    )
    api_keys: List["ApiKey"] = Relationship(
        sa_relationship=relationship("ApiKey", back_populates="tenant")
    )
    files: List["File"] = Relationship(
        sa_relationship=relationship("File", back_populates="tenant")
    )
    subscription_tier: Optional["LicenseTier"] = Relationship()


class TenantCreate(SQLModel):
    """Schema for creating a tenant"""

    name: str = Field(description="Tenant name")
    slug: str = Field(description="URL-friendly tenant identifier")
    max_users: int = Field(default=10, description="Maximum number of users allowed")
    description: Optional[str] = Field(default=None, description="Optional tenant description")
    is_active: bool = Field(default=True, description="Whether tenant is active")


class TenantRead(SQLModel):
    """Schema for reading a tenant"""

    id: UUIDstr
    name: str
    slug: str
    is_active: bool
    max_users: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    license_pools: dict[str, Any] = Field(default_factory=dict)
    subscription_tier_id: Optional[UUIDstr] = None
    subscription_license_count: int = Field(default=0)
    subscription_status: Optional[str] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    subscription_renewal_date: Optional[datetime] = None
    subscription_payment_method_id: Optional[str] = None
    subscription_amount: Optional[Decimal] = None
    subscription_currency: str = Field(default="USD")


class TenantUpdate(SQLModel):
    """Schema for updating a tenant"""

    name: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None
    max_users: Optional[int] = None
    description: Optional[str] = None
    license_pools: Optional[dict[str, Any]] = None
    subscription_tier_id: Optional[UUIDstr] = None
    subscription_license_count: Optional[int] = None
    subscription_status: Optional[str] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    subscription_renewal_date: Optional[datetime] = None
    subscription_payment_method_id: Optional[str] = None
    subscription_amount: Optional[Decimal] = None
    subscription_currency: Optional[str] = None
