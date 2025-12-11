"""Feature control database models."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, Numeric
from sqlmodel import Field, SQLModel

from kluisz.schema.serialize import UUIDstr


class FeatureRegistry(SQLModel, table=True):
    """Master registry of all available features."""

    __tablename__ = "feature_registry"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Identification
    feature_key: str = Field(unique=True, index=True, max_length=255)
    feature_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, nullable=True)

    # Categorization
    category: str = Field(index=True, max_length=50)  # models, components, integrations, ui, api, limits
    subcategory: Optional[str] = Field(default=None, nullable=True, max_length=50)

    # Feature type and default
    feature_type: str = Field(default="boolean", max_length=20)  # boolean, integer, string, json
    default_value: dict = Field(
        default_factory=lambda: {"enabled": False},
        sa_column=Column(JSON),
    )

    # Metadata
    is_premium: bool = Field(default=False)
    requires_setup: bool = Field(default=False)
    depends_on: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    conflicts_with: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # UI hints
    display_order: int = Field(default=0)
    icon: Optional[str] = Field(default=None, nullable=True, max_length=50)
    help_url: Optional[str] = Field(default=None, nullable=True, max_length=500)

    # Status
    is_active: bool = Field(default=True, index=True)
    is_deprecated: bool = Field(default=False)
    deprecated_message: Optional[str] = Field(default=None, nullable=True)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Note: Not a FK constraint to avoid circular dependency
    # Validation happens at application level
    created_by: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        description="User who created this feature (UUID reference, not FK)",
    )


class LicenseTierFeatures(SQLModel, table=True):
    """Features included in each license tier."""

    __tablename__ = "license_tier_features"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    license_tier_id: UUIDstr = Field(foreign_key="license_tier.id", index=True)
    feature_key: str = Field(foreign_key="feature_registry.feature_key", max_length=255)

    # Feature value for this tier
    feature_value: dict = Field(sa_column=Column(JSON))

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Note: Not a FK constraint to avoid circular dependency between license_tier ↔ user
    # license_tier_features depends on license_tier, user depends on license_tier
    # Adding FK here would create: user → license_tier ← license_tier_features → user (cycle)
    created_by: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        description="User who created this feature config (UUID reference, not FK)",
    )

    class Config:
        """SQLModel configuration."""

        table_args = ({"sqlite_autoincrement": True},)


class ModelRegistry(SQLModel, table=True):
    """Registry of available AI models."""

    __tablename__ = "model_registry"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Model identification
    provider: str = Field(index=True, max_length=50)
    model_id: str = Field(max_length=100)
    model_name: str = Field(max_length=255)

    # Categorization
    model_type: str = Field(max_length=50)  # chat, completion, embedding, image, audio
    model_family: Optional[str] = Field(default=None, nullable=True, max_length=50)

    # Capabilities
    supports_tools: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    supports_streaming: bool = Field(default=True)
    max_tokens: Optional[int] = Field(default=None, nullable=True)
    context_window: Optional[int] = Field(default=None, nullable=True)

    # Pricing (per 1K tokens)
    input_price_per_1k: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(10, 6), nullable=True),
    )
    output_price_per_1k: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(10, 6), nullable=True),
    )

    # Feature key mapping
    feature_key: str = Field(
        foreign_key="feature_registry.feature_key",
        index=True,
        max_length=255,
    )

    # Status
    is_active: bool = Field(default=True, index=True)
    is_deprecated: bool = Field(default=False)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComponentRegistry(SQLModel, table=True):
    """Registry of available flow components.
    
    Components can be:
    - Feature-gated: feature_key is set, component requires feature to be enabled
    - Public: feature_key is NULL, component is always available (no gating)
    """

    __tablename__ = "component_registry"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Component identification
    component_key: str = Field(unique=True, index=True, max_length=255)
    component_name: str = Field(max_length=255)
    display_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, nullable=True)

    # Categorization
    category: str = Field(index=True, max_length=50)
    subcategory: Optional[str] = Field(default=None, nullable=True, max_length=50)

    # Feature key mapping
    # NULL = public component (always available, no feature gating)
    # Non-NULL = feature-gated component (requires feature to be enabled)
    # FK constraint enforced at DB level for non-NULL values
    feature_key: Optional[str] = Field(
        default=None,
        nullable=True,
        foreign_key="feature_registry.feature_key",
        max_length=255,
    )

    # Requirements
    required_features: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Metadata
    icon: Optional[str] = Field(default=None, nullable=True, max_length=50)
    documentation_url: Optional[str] = Field(default=None, nullable=True, max_length=500)
    is_beta: bool = Field(default=False)

    # Status
    is_active: bool = Field(default=True)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IntegrationRegistry(SQLModel, table=True):
    """Registry of available third-party integrations."""

    __tablename__ = "integration_registry"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # Integration identification
    integration_key: str = Field(unique=True, index=True, max_length=100)
    integration_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, nullable=True)

    # Categorization
    category: str = Field(index=True, max_length=50)  # observability, vector_store, database, etc.

    # Feature key mapping
    feature_key: str = Field(
        foreign_key="feature_registry.feature_key",
        max_length=255,
    )

    # Configuration schema
    config_schema: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Requirements
    required_features: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Metadata
    icon: Optional[str] = Field(default=None, nullable=True, max_length=50)
    documentation_url: Optional[str] = Field(default=None, nullable=True, max_length=500)
    setup_guide_url: Optional[str] = Field(default=None, nullable=True, max_length=500)

    # Status
    is_active: bool = Field(default=True)
    is_beta: bool = Field(default=False)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TenantIntegrationConfig(SQLModel, table=True):
    """Tenant-specific integration configurations."""

    __tablename__ = "tenant_integration_configs"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    tenant_id: UUIDstr = Field(foreign_key="tenant.id", index=True)
    integration_key: str = Field(foreign_key="integration_registry.integration_key", max_length=100)

    # Configuration (encrypted sensitive fields)
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    encrypted_config: Optional[bytes] = Field(default=None, nullable=True)

    # Status
    is_enabled: bool = Field(default=False, index=True)
    last_health_check: Optional[datetime] = Field(default=None, nullable=True)
    health_status: Optional[str] = Field(
        default=None,
        nullable=True,
        max_length=20,
        # Valid values: 'healthy', 'degraded', 'unhealthy', NULL
        # CHECK constraint enforced at DB level
    )

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Note: Not a FK constraint to avoid circular dependencies
    # tenant_integration_configs depends on tenant, which depends on license_tier
    # user depends on both tenant and license_tier
    created_by: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        description="User who created this config (UUID reference, not FK)",
    )


class FeatureAuditLog(SQLModel, table=True):
    """Audit log for feature changes."""

    __tablename__ = "feature_audit_log"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # What changed
    entity_type: str = Field(max_length=50)  # tenant, tier, registry
    entity_id: UUIDstr
    feature_key: str = Field(max_length=255)

    # Change details
    action: str = Field(max_length=20)  # enable, disable, update, request
    old_value: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    new_value: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Who and when
    # Note: Not a FK constraint to avoid circular dependencies
    performed_by: Optional[UUIDstr] = Field(
        default=None,
        nullable=True,
        description="User who performed this action (UUID reference, not FK)",
    )
    performed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Context
    reason: Optional[str] = Field(default=None, nullable=True)
    ip_address: Optional[str] = Field(default=None, nullable=True, max_length=45)
    user_agent: Optional[str] = Field(default=None, nullable=True)


# ============================================
# Pydantic Schemas for API
# ============================================


class FeatureRegistryRead(SQLModel):
    """Schema for reading a feature from registry."""

    feature_key: str
    feature_name: str
    description: Optional[str]
    category: str
    subcategory: Optional[str]
    feature_type: str
    default_value: dict
    is_premium: bool
    requires_setup: bool
    depends_on: list[str]
    display_order: int
    icon: Optional[str]
    help_url: Optional[str]
    is_active: bool
    is_deprecated: bool


class LicenseTierFeaturesRead(SQLModel):
    """Schema for reading tier features."""

    tier_id: str
    features: dict[str, Any]


class FeatureCheckResponse(SQLModel):
    """Schema for feature check response."""

    feature_key: str
    enabled: bool
    value: Optional[Any] = None
    source: str  # default, tier
    expires_at: Optional[str] = None


