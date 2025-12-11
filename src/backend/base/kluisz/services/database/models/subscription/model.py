from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List
from uuid import uuid4

from sqlalchemy import Numeric
from sqlalchemy import Column as SAColumn
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.license_tier.model import LicenseTier
    from kluisz.services.database.models.subscription_history.model import SubscriptionHistory
    from kluisz.services.database.models.tenant.model import Tenant


class SubscriptionBase(SQLModel):
    """Base subscription model with common fields"""

    # Subscription Details
    tier_id: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        foreign_key="license_tier.id",
        index=True,
        description="License tier for this subscription",
    )
    license_count: int = Field(
        default=0,
        ge=0,
        description="Number of licenses in this subscription",
    )
    monthly_credits: int = Field(
        default=0,
        ge=0,
        description="Monthly credits allocated per subscription",
    )

    # Billing
    amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=SAColumn(Numeric(10, 2)),
        ge=Decimal("0.00"),
        description="Monthly subscription amount",
    )
    currency: str = Field(
        default="USD",
        description="Currency code (e.g., USD, EUR)",
    )
    billing_cycle: str = Field(
        default="monthly",
        description="Billing cycle: monthly or yearly",
    )

    # Status
    status: str = Field(
        index=True,
        description="Subscription status: active, cancelled, past_due, trialing, expired",
    )

    # Dates
    start_date: datetime = Field(
        description="Subscription start date",
    )
    end_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Subscription end date (None = ongoing)",
    )
    renewal_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        index=True,
        description="Next renewal date",
    )
    cancelled_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Cancellation timestamp",
    )

    # Payment
    payment_method_id: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Stripe payment method ID",
    )
    last_payment_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Last successful payment date",
    )
    next_payment_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        index=True,
        description="Next payment due date",
    )


class Subscription(SubscriptionBase, table=True):  # type: ignore[call-arg]
    """Subscription database model"""

    __tablename__ = "subscription"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUIDstr = Field(
        foreign_key="tenant.id",
        index=True,
        description="Tenant this subscription belongs to",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Subscription creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # Relationships
    tenant: "Tenant" = Relationship(back_populates="subscriptions")
    tier: Optional["LicenseTier"] = Relationship()
    history: List["SubscriptionHistory"] = Relationship(
        sa_relationship=relationship("SubscriptionHistory", back_populates="subscription")
    )


class SubscriptionCreate(SQLModel):
    """Schema for creating a subscription"""

    tenant_id: UUIDstr
    tier_id: Optional[UUIDstr] = None
    license_count: int = Field(default=0, ge=0)
    monthly_credits: int = Field(default=0, ge=0)
    amount: Decimal = Field(ge=Decimal("0.00"))
    currency: str = Field(default="USD")
    billing_cycle: str = Field(default="monthly")
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    payment_method_id: Optional[str] = None
    next_payment_date: Optional[datetime] = None


class SubscriptionRead(SQLModel):
    """Schema for reading a subscription"""

    id: UUIDstr
    tenant_id: UUIDstr
    tier_id: Optional[UUIDstr]
    license_count: int
    monthly_credits: int
    amount: Decimal
    currency: str
    billing_cycle: str
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    renewal_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    payment_method_id: Optional[str]
    last_payment_date: Optional[datetime]
    next_payment_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SubscriptionUpdate(SQLModel):
    """Schema for updating a subscription"""

    tier_id: Optional[UUIDstr] = None
    license_count: Optional[int] = None
    monthly_credits: Optional[int] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    billing_cycle: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    payment_method_id: Optional[str] = None
    last_payment_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None

