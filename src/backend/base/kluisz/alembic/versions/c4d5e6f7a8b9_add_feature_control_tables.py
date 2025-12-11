"""Add feature control tables

Revision ID: c4d5e6f7a8b9
Revises: 182e5471b900, 3162e83e485f, d37bc4322900
Create Date: 2025-01-15 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = ("182e5471b900", "3162e83e485f", "d37bc4322900")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Helper functions
    def safe_create_table(table_name, *args, **kwargs):
        if table_name not in existing_tables:
            try:
                op.create_table(table_name, *args, **kwargs)
            except Exception:
                pass

    def safe_create_index(index_name, table_name, columns, **kwargs):
        try:
            existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing_indexes:
                op.create_index(index_name, table_name, columns, **kwargs)
        except Exception:
            pass

    # ============================================
    # FEATURE REGISTRY (Source of Truth)
    # ============================================
    safe_create_table(
        "feature_registry",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("feature_key", sa.String(255), nullable=False),
        sa.Column("feature_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(50), nullable=True),
        sa.Column("feature_type", sa.String(20), nullable=False, server_default="boolean"),
        sa.Column("default_value", sa.JSON(), nullable=False),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("requires_setup", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("depends_on", sa.JSON(), nullable=True),
        sa.Column("conflicts_with", sa.JSON(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("help_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_deprecated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("deprecated_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feature_key"),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
    )
    safe_create_index("idx_feature_registry_category", "feature_registry", ["category"], unique=False)
    safe_create_index("idx_feature_registry_key", "feature_registry", ["feature_key"], unique=True)

    # ============================================
    # LICENSE TIER FEATURES (What each tier includes)
    # ============================================
    safe_create_table(
        "license_tier_features",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("license_tier_id", sa.String(), nullable=False),
        sa.Column("feature_key", sa.String(255), nullable=False),
        sa.Column("feature_value", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["license_tier_id"], ["license_tier.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feature_key"], ["feature_registry.feature_key"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.UniqueConstraint("license_tier_id", "feature_key"),
    )
    safe_create_index("idx_tier_features_tier", "license_tier_features", ["license_tier_id"], unique=False)

    # ============================================
    # MODEL REGISTRY (Available Models)
    # ============================================
    safe_create_table(
        "model_registry",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("model_family", sa.String(50), nullable=True),
        sa.Column("supports_tools", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("supports_vision", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("input_price_per_1k", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("output_price_per_1k", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("feature_key", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_deprecated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "model_id"),
    )
    safe_create_index("idx_model_registry_provider", "model_registry", ["provider"], unique=False)
    safe_create_index("idx_model_registry_feature", "model_registry", ["feature_key"], unique=False)

    # ============================================
    # COMPONENT REGISTRY (Available Components)
    # ============================================
    safe_create_table(
        "component_registry",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("component_key", sa.String(255), nullable=False),
        sa.Column("component_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(50), nullable=True),
        sa.Column("feature_key", sa.String(255), nullable=True),
        sa.Column("required_features", sa.JSON(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("documentation_url", sa.String(500), nullable=True),
        sa.Column("is_beta", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("component_key"),
    )
    safe_create_index("idx_component_registry_category", "component_registry", ["category"], unique=False)
    safe_create_index("idx_component_registry_feature", "component_registry", ["feature_key"], unique=False)

    # ============================================
    # INTEGRATION REGISTRY
    # ============================================
    safe_create_table(
        "integration_registry",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("integration_key", sa.String(100), nullable=False),
        sa.Column("integration_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("feature_key", sa.String(255), nullable=False),
        sa.Column("config_schema", sa.JSON(), nullable=True),
        sa.Column("required_features", sa.JSON(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("documentation_url", sa.String(500), nullable=True),
        sa.Column("setup_guide_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_beta", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_key"),
    )

    # ============================================
    # TENANT INTEGRATION CONFIGS
    # ============================================
    safe_create_table(
        "tenant_integration_configs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("integration_key", sa.String(100), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("encrypted_config", sa.LargeBinary(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("health_status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["integration_key"], ["integration_registry.integration_key"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.UniqueConstraint("tenant_id", "integration_key"),
    )

    # ============================================
    # FEATURE AUDIT LOG
    # ============================================
    safe_create_table(
        "feature_audit_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("feature_key", sa.String(255), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("performed_by", sa.String(), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["performed_by"], ["user.id"]),
    )
    safe_create_index("idx_feature_audit_entity", "feature_audit_log", ["entity_type", "entity_id"], unique=False)
    safe_create_index("idx_feature_audit_time", "feature_audit_log", ["performed_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_feature_audit_time", table_name="feature_audit_log")
    op.drop_index("idx_feature_audit_entity", table_name="feature_audit_log")
    op.drop_table("feature_audit_log")
    op.drop_table("tenant_integration_configs")
    op.drop_table("integration_registry")
    op.drop_index("idx_component_registry_feature", table_name="component_registry")
    op.drop_index("idx_component_registry_category", table_name="component_registry")
    op.drop_table("component_registry")
    op.drop_index("idx_model_registry_feature", table_name="model_registry")
    op.drop_index("idx_model_registry_provider", table_name="model_registry")
    op.drop_table("model_registry")
    op.drop_index("idx_tier_features_tier", table_name="license_tier_features")
    op.drop_table("license_tier_features")
    op.drop_index("idx_feature_registry_key", table_name="feature_registry")
    op.drop_index("idx_feature_registry_category", table_name="feature_registry")
    op.drop_table("feature_registry")


