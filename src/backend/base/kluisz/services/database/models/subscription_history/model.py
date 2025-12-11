
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Numeric, Text
from sqlalchemy import Column as SAColumn
from sqlmodel import Field, Relationship, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.subscription.model import Subscription
    from kluisz.services.database.models.user.model import User


class SubscriptionHistoryBase(SQLModel):
    """Base subscription history model with common fields"""

    subscription_id: UUIDstr = Field(
        foreign_key="subscription.id",
        index=True,
        description="Subscription this history entry belongs to",
    )
    tenant_id: UUIDstr = Field(
        index=True,
        description="Tenant for this history entry",
    )

    # Change Details
    action: str = Field(
        index=True,
        description="Action type: created, upgraded, downgraded, cancelled, renewed, payment_failed",
    )
    old_tier_id: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        description="Previous tier ID (for upgrades/downgrades)",
    )
    new_tier_id: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        description="New tier ID (for upgrades/downgrades)",
    )
    old_license_count: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Previous license count",
    )
    new_license_count: Optional[int] = Field(
        default=None,
        nullable=True,
        description="New license count",
    )
    old_amount: Optional[Decimal] = Field(
        default=None,
        sa_column=SAColumn(Numeric(10, 2), nullable=True),
        description="Previous subscription amount",
    )
    new_amount: Optional[Decimal] = Field(
        default=None,
        sa_column=SAColumn(Numeric(10, 2), nullable=True),
        description="New subscription amount",
    )

    # Metadata
    reason: Optional[str] = Field(
        default=None,
        sa_column=SAColumn(Text, nullable=True),
        description="Reason for the change",
    )
    changed_by: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        foreign_key="user.id",
        description="User who made the change",
    )


class SubscriptionHistory(SubscriptionHistoryBase, table=True):  # type: ignore[call-arg]
    """Subscription history database model"""

    __tablename__ = "subscription_history"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="History entry creation timestamp",
    )

    # Relationships
    subscription: "Subscription" = Relationship(back_populates="history")
    changed_by_user: Optional["User"] = Relationship()


class SubscriptionHistoryCreate(SQLModel):
    """Schema for creating subscription history"""

    subscription_id: UUIDstr
    tenant_id: UUIDstr
    action: str
    old_tier_id: Optional[UUIDstr] = None
    new_tier_id: Optional[UUIDstr] = None
    old_license_count: Optional[int] = None
    new_license_count: Optional[int] = None
    old_amount: Optional[Decimal] = None
    new_amount: Optional[Decimal] = None
    reason: Optional[str] = None
    changed_by: Optional[UUIDstr] = None


class SubscriptionHistoryRead(SQLModel):
    """Schema for reading subscription history"""

    id: UUIDstr
    subscription_id: UUIDstr
    tenant_id: UUIDstr
    action: str
    old_tier_id: Optional[UUIDstr]
    new_tier_id: Optional[UUIDstr]
    old_license_count: Optional[int]
    new_license_count: Optional[int]
    old_amount: Optional[Decimal]
    new_amount: Optional[Decimal]
    reason: Optional[str]
    changed_by: Optional[UUIDstr]
    created_at: datetime

