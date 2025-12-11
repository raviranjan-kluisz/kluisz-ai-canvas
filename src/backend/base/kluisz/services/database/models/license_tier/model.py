
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, Numeric
from sqlmodel import Field, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.user.model import User


class LicenseTierBase(SQLModel):
    """Base license tier model with common fields"""

    name: str = Field(index=True, unique=True, description="License tier name (e.g., Starter, Professional, Enterprise)")
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Optional tier description",
    )

    # Pricing
    token_price_per_1000: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2)),
        description="Base token price per 1000 tokens",
    )
    credits_per_usd: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2)),
        description="Credits per USD (e.g., 100 credits per $1)",
    )
    pricing_multiplier: Decimal = Field(
        default=Decimal("1.00"),
        sa_column=Column(Numeric(10, 2)),
        description="Cost multiplier (1.00 = standard, 0.95 = 5% discount, 1.10 = 10% markup)",
    )

    # Default Credits
    default_credits: int = Field(
        default=0,
        ge=0,
        description="Default credits allocated when license is assigned",
    )
    default_credits_per_month: Optional[int] = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Default monthly credits for subscriptions (None = one-time allocation)",
    )

    # Limits (NULL = unlimited)
    max_users: Optional[int] = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Maximum number of users allowed (None = unlimited)",
    )
    max_flows: Optional[int] = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Maximum number of flows allowed (None = unlimited)",
    )
    max_api_calls: Optional[int] = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Maximum API calls per billing cycle (None = unlimited)",
    )

    # Features
    features: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Feature flags and tier-specific features",
    )

    # Status
    is_active: bool = Field(
        default=True,
        index=True,
        description="Whether tier is active (can be assigned)",
    )


class LicenseTier(LicenseTierBase, table=True):  # type: ignore[call-arg]
    """License tier database model"""

    __tablename__ = "license_tier"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    created_by: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        # Note: Not a FK constraint to avoid circular dependency with user table
        # Validation happens at application level
        description="User who created this tier (UUID reference, not FK)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Tier creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )


class LicenseTierCreate(SQLModel):
    """Schema for creating a license tier"""

    name: str = Field(description="License tier name")
    description: Optional[str] = None
    token_price_per_1000: Decimal = Field(default=Decimal("0.00"))
    credits_per_usd: Decimal = Field(default=Decimal("0.00"))
    pricing_multiplier: Decimal = Field(default=Decimal("1.00"))
    default_credits: int = Field(default=0, ge=0)
    default_credits_per_month: Optional[int] = Field(default=None, ge=0)
    max_users: Optional[int] = Field(default=None, ge=0)
    max_flows: Optional[int] = Field(default=None, ge=0)
    max_api_calls: Optional[int] = Field(default=None, ge=0)
    features: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)


class LicenseTierRead(SQLModel):
    """Schema for reading a license tier"""

    id: UUIDstr
    name: str
    description: Optional[str]
    token_price_per_1000: Decimal
    credits_per_usd: Decimal
    pricing_multiplier: Decimal
    default_credits: int
    default_credits_per_month: Optional[int]
    max_users: Optional[int]
    max_flows: Optional[int]
    max_api_calls: Optional[int]
    features: dict[str, Any]
    is_active: bool
    created_by: Optional[UUIDstr]
    created_at: datetime
    updated_at: datetime


class LicenseTierUpdate(SQLModel):
    """Schema for updating a license tier"""

    name: Optional[str] = None
    description: Optional[str] = None
    token_price_per_1000: Optional[Decimal] = None
    credits_per_usd: Optional[Decimal] = None
    pricing_multiplier: Optional[Decimal] = None
    default_credits: Optional[int] = None
    default_credits_per_month: Optional[int] = None
    max_users: Optional[int] = None
    max_flows: Optional[int] = None
    max_api_calls: Optional[int] = None
    features: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None

