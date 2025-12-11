
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.tenant.model import Tenant


class LicenseTier(str, Enum):
    """License tier enumeration - 3 tiers"""

    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseBase(SQLModel):
    """Base license model with common fields"""

    license_type: str = Field(index=True, description="License type identifier")
    tier: LicenseTier = Field(
        default=LicenseTier.BASIC,
        index=True,
        description="License tier: basic, pro, or enterprise",
    )
    max_users: Optional[int] = Field(
        default=10,
        nullable=True,
        description="Maximum number of users allowed (None = unlimited)",
    )
    max_flows: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Maximum number of flows allowed (None = unlimited)",
    )
    max_api_calls: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Maximum API calls per billing cycle (None = unlimited)",
    )

    # Credits system
    credits: int = Field(
        default=0,
        description="Total credits allocated to this license",
    )
    credits_per_month: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Credits allocated per month (None = one-time allocation)",
    )
    credits_used: int = Field(
        default=0,
        description="Credits consumed so far",
    )

    # Features and limits
    features: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Feature flags and tier-specific features",
    )

    # Billing
    billing_cycle: str = Field(
        default="monthly",
        description="Billing cycle: monthly, yearly, or one-time",
    )
    price: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2)),
        description="License price",
    )

    # Dates
    start_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="License start date",
    )
    end_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="License end date (None = perpetual)",
    )

    is_active: bool = Field(default=True, index=True, description="Whether license is currently active")


class License(LicenseBase, table=False):  # type: ignore[call-arg]
    """License database model - DISABLED: Merged into user table"""
    
    # This table is disabled - license information is now stored directly in the user table
    # and managed via pools in tenant.license_pools JSON
    __tablename__ = "license"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUIDstr = Field(
        foreign_key="tenant.id",
        index=True,
        description="Tenant this license belongs to",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="License creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # Relationships removed - License model is disabled, functionality merged into user table

    @property
    def credits_remaining(self) -> int:
        """Calculate remaining credits"""
        return max(0, self.credits - self.credits_used)

    @property
    def is_expired(self) -> bool:
        """Check if license has expired"""
        if self.end_date is None:
            return False
        return datetime.now(timezone.utc) > self.end_date

    @property
    def is_valid(self) -> bool:
        """Check if license is valid (active and not expired)"""
        return self.is_active and not self.is_expired


class LicenseCreate(SQLModel):
    """Schema for creating a license"""

    tenant_id: UUIDstr
    license_type: str
    tier: LicenseTier = Field(default=LicenseTier.BASIC)
    max_users: Optional[int] = None
    max_flows: Optional[int] = None
    max_api_calls: Optional[int] = None
    credits: int = Field(default=0)
    credits_per_month: Optional[int] = None
    features: dict[str, Any] = Field(default_factory=dict)
    billing_cycle: str = Field(default="monthly")
    price: Decimal = Field(default=Decimal("0.00"))
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = Field(default=True)


class LicenseRead(SQLModel):
    """Schema for reading a license"""

    id: UUIDstr
    tenant_id: UUIDstr
    license_type: str
    tier: LicenseTier
    max_users: Optional[int]
    max_flows: Optional[int]
    max_api_calls: Optional[int]
    credits: int
    credits_per_month: Optional[int]
    credits_used: int
    features: dict[str, Any]
    billing_cycle: str
    price: Decimal
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LicenseUpdate(SQLModel):
    """Schema for updating a license"""

    license_type: Optional[str] = None
    tier: Optional[LicenseTier] = None
    max_users: Optional[int] = None
    max_flows: Optional[int] = None
    max_api_calls: Optional[int] = None
    credits: Optional[int] = None
    credits_per_month: Optional[int] = None
    credits_used: Optional[int] = None
    features: Optional[dict[str, Any]] = None
    billing_cycle: Optional[str] = None
    price: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
