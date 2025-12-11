from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Numeric, UniqueConstraint
from sqlalchemy import Column as SAColumn
from sqlmodel import Field, Relationship, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.tenant.model import Tenant
    from kluisz.services.database.models.user.model import User


class UserUsageStatsBase(SQLModel):
    """Base user usage statistics model"""

    # Time Period
    period_start: datetime = Field(index=True, description="Period start timestamp")
    period_end: datetime = Field(index=True, description="Period end timestamp")

    # Aggregated Stats
    credits_used: int = Field(
        default=0,
        ge=0,
        description="Credits used in this period",
    )
    traces_count: int = Field(
        default=0,
        ge=0,
        description="Number of traces in this period",
    )
    cost_usd: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=SAColumn(Numeric(10, 2)),
        description="Cost in USD for this period",
    )


class UserUsageStats(UserUsageStatsBase, table=False):  # type: ignore[call-arg]
    """User usage statistics database model.
    
    DEPRECATED: This table is disabled. Analytics now use the transaction table directly,
    which is populated in real-time by the metering callback.
    
    See: kluisz.services.analytics.service.AnalyticsService
    """

    __tablename__ = "user_usage_stats"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    user_id: UUIDstr = Field(
        foreign_key="user.id",
        index=True,
        description="User these stats belong to",
    )
    tenant_id: UUIDstr = Field(
        foreign_key="tenant.id",
        index=True,
        description="Tenant for aggregation",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Stats creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # Note: Relationships removed as table is disabled
    # user: "User" = Relationship(back_populates="usage_stats")
    # tenant: "Tenant" = Relationship(back_populates="user_usage_stats")


class UserUsageStatsCreate(SQLModel):
    """Schema for creating user usage stats"""

    user_id: UUIDstr
    tenant_id: UUIDstr
    period_start: datetime
    period_end: datetime
    credits_used: int = Field(default=0, ge=0)
    traces_count: int = Field(default=0, ge=0)
    cost_usd: Decimal = Field(default=Decimal("0.00"))


class UserUsageStatsRead(SQLModel):
    """Schema for reading user usage stats"""

    id: UUIDstr
    user_id: UUIDstr
    tenant_id: UUIDstr
    period_start: datetime
    period_end: datetime
    credits_used: int
    traces_count: int
    cost_usd: Decimal
    created_at: datetime
    updated_at: datetime


class UserUsageStatsUpdate(SQLModel):
    """Schema for updating user usage stats"""

    credits_used: int | None = None
    traces_count: int | None = None
    cost_usd: Decimal | None = None

