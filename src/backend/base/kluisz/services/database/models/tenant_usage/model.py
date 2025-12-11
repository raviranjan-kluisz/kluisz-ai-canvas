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


class TenantUsageStatsBase(SQLModel):
    """Base tenant usage statistics model"""

    # Time Period
    period_start: datetime = Field(index=True, description="Period start timestamp")
    period_end: datetime = Field(index=True, description="Period end timestamp")

    # Aggregated Stats
    total_credits_used: int = Field(
        default=0,
        ge=0,
        description="Total credits used in this period",
    )
    total_traces: int = Field(
        default=0,
        ge=0,
        description="Total number of traces in this period",
    )
    total_cost_usd: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=SAColumn(Numeric(10, 2)),
        description="Total cost in USD for this period",
    )
    active_users_count: int = Field(
        default=0,
        ge=0,
        description="Number of active users in this period",
    )


class TenantUsageStats(TenantUsageStatsBase, table=False):  # type: ignore[call-arg]
    """Tenant usage statistics database model.
    
    DEPRECATED: This table is disabled. Analytics now use the transaction table directly,
    which is populated in real-time by the metering callback.
    
    See: kluisz.services.analytics.service.AnalyticsService
    """

    __tablename__ = "tenant_usage_stats"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUIDstr = Field(
        foreign_key="tenant.id",
        index=True,
        description="Tenant these stats belong to",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Stats creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # Note: Relationship removed as table is disabled
    # tenant: "Tenant" = Relationship(back_populates="usage_stats")


class TenantUsageStatsCreate(SQLModel):
    """Schema for creating tenant usage stats"""

    tenant_id: UUIDstr
    period_start: datetime
    period_end: datetime
    total_credits_used: int = Field(default=0, ge=0)
    total_traces: int = Field(default=0, ge=0)
    total_cost_usd: Decimal = Field(default=Decimal("0.00"))
    active_users_count: int = Field(default=0, ge=0)


class TenantUsageStatsRead(SQLModel):
    """Schema for reading tenant usage stats"""

    id: UUIDstr
    tenant_id: UUIDstr
    period_start: datetime
    period_end: datetime
    total_credits_used: int
    total_traces: int
    total_cost_usd: Decimal
    active_users_count: int
    created_at: datetime
    updated_at: datetime


class TenantUsageStatsUpdate(SQLModel):
    """Schema for updating tenant usage stats"""

    total_credits_used: int | None = None
    total_traces: int | None = None
    total_cost_usd: Decimal | None = None
    active_users_count: int | None = None
