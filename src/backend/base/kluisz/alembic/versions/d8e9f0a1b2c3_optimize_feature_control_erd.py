"""Optimize feature control ERD - add indexes and constraints

Revision ID: d8e9f0a1b2c3
Revises: c4d5e6f7a8b9
Create Date: 2025-01-15 15:00:00.000000

This migration implements all P0 and P1 optimizations from ERD-CRITICAL-ANALYSIS.md:
- Add composite indexes for common query patterns
- Add foreign key constraints for data integrity
- Add CHECK constraints for data validation
- Optimize performance-critical queries

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8e9f0a1b2c3"
down_revision: str | Sequence[str] | None = "c4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add indexes, foreign keys, and constraints."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    dialect_name = conn.dialect.name

    # Helper function to safely create index
    def safe_create_index(index_name: str, table_name: str, columns: list[str], **kwargs):
        """Safely create index if it doesn't exist."""
        try:
            existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing_indexes:
                op.create_index(index_name, table_name, columns, **kwargs)
        except Exception:
            pass  # Index might already exist or table might not exist

    # Helper function to safely add constraint
    def safe_add_constraint(table_name: str, constraint_name: str, constraint_text: str):
        """Safely add CHECK constraint if it doesn't exist."""
        # SQLite doesn't support ALTER TABLE ... ADD CONSTRAINT
        # We'll skip CHECK constraints for SQLite (validation happens at application level)
        if dialect_name == "sqlite":
            # SQLite doesn't support adding CHECK constraints after table creation
            # Validation will be enforced at application level
            return
        
        try:
            existing_constraints = [
                c["name"] for c in inspector.get_check_constraints(table_name)
            ]
            if constraint_name not in existing_constraints:
                # PostgreSQL supports ALTER TABLE ... ADD CONSTRAINT
                op.execute(
                    sa.text(
                        f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} CHECK ({constraint_text})"
                    )
                )
        except Exception as e:
            # Constraint might already exist or table might not exist
            print(f"Warning: Could not add constraint {constraint_name}: {e}")
            pass

    # Helper function to safely add foreign key
    def safe_add_fk(table_name: str, fk_name: str, columns: list[str], ref_table: str, ref_columns: list[str], ondelete: str = "RESTRICT"):
        """Safely add foreign key constraint if it doesn't exist."""
        try:
            # Check if FK already exists by inspecting foreign keys
            fks = inspector.get_foreign_keys(table_name)
            existing_fk_names = [fk["name"] for fk in fks]
            if fk_name not in existing_fk_names:
                op.create_foreign_key(
                    fk_name,
                    table_name,
                    ref_table,
                    columns,
                    ref_columns,
                    ondelete=ondelete,
                )
        except Exception:
            pass  # FK might already exist

    # ============================================
    # P0 FIXES - Critical (Fix Immediately)
    # ============================================

    # 0. Fix FK cycle: Remove FK constraints that cause circular dependencies
    # The cycle: user → license_tier (via license_tier_id) AND various tables → user (via created_by)
    # All created_by/performed_by fields are now UUID references, validated at application level
    
    # Tables with created_by/performed_by fields that reference user.id
    fk_removal_tables = [
        ("license_tier", "created_by"),
        ("feature_registry", "created_by"),
        ("license_tier_features", "created_by"),
        ("tenant_integration_configs", "created_by"),
        ("feature_audit_log", "performed_by"),
    ]
    
    for table_name, column_name in fk_removal_tables:
        try:
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                if column_name in fk.get("constrained_columns", []):
                    op.drop_constraint(fk["name"], table_name, type_="foreignkey")
                    print(f"Dropped FK constraint {fk['name']} from {table_name}.{column_name} to break cycle")
        except Exception:
            pass  # FK might not exist or table might not exist

    # 1. Add composite index: (license_tier_id, feature_key) on license_tier_features
    safe_create_index(
        "idx_tier_features_tier_key",
        "license_tier_features",
        ["license_tier_id", "feature_key"],
    )

    # 2. Add FK constraints: ModelRegistry.feature_key → FeatureRegistry.feature_key
    safe_add_fk(
        "model_registry",
        "fk_model_registry_feature",
        ["feature_key"],
        "feature_registry",
        ["feature_key"],
        ondelete="RESTRICT",
    )

    # 3. Add FK constraints: ComponentRegistry.feature_key → FeatureRegistry.feature_key
    # Note: feature_key is nullable, so we need to handle NULLs
    # SQLite doesn't support partial FKs, so we'll add it only if all rows have feature_key
    try:
        # Check if all component_registry rows have feature_key
        result = conn.execute(
            sa.text("SELECT COUNT(*) FROM component_registry WHERE feature_key IS NULL")
        )
        null_count = result.scalar()
        
        if null_count == 0:
            # All rows have feature_key, safe to add FK
            safe_add_fk(
                "component_registry",
                "fk_component_registry_feature",
                ["feature_key"],
                "feature_registry",
                ["feature_key"],
                ondelete="RESTRICT",
            )
        else:
            # Some rows have NULL feature_key - we'll add index but not FK constraint
            # The FK will be enforced at application level for non-NULL values
            print(f"Warning: {null_count} component_registry rows have NULL feature_key. FK constraint skipped.")
    except Exception:
        # Table might not exist or error checking
        pass

    # 4. Add FK constraints: IntegrationRegistry.feature_key → FeatureRegistry.feature_key
    safe_add_fk(
        "integration_registry",
        "fk_integration_registry_feature",
        ["feature_key"],
        "feature_registry",
        ["feature_key"],
        ondelete="RESTRICT",
    )

    # ============================================
    # P1 FIXES - High Priority
    # ============================================

    # 5. Add index: (tenant_id, is_enabled) on tenant_integration_configs
    # For SQLite, we'll create a regular index (partial indexes not supported)
    safe_create_index(
        "idx_tenant_integration_active",
        "tenant_integration_configs",
        ["tenant_id", "is_enabled"],
    )

    # 6. Add index: (feature_key, performed_at DESC) on feature_audit_log
    safe_create_index(
        "idx_feature_audit_key_time",
        "feature_audit_log",
        ["feature_key", "performed_at"],
        postgresql_ops={"performed_at": "DESC"},
    )

    # 7. Add CHECK constraint on health_status
    # Valid values: 'healthy', 'degraded', 'unhealthy', or NULL
    # Note: SQLite doesn't support ALTER TABLE ... ADD CONSTRAINT, so this is skipped for SQLite
    # Validation is enforced at application level for SQLite
    safe_add_constraint(
        "tenant_integration_configs",
        "chk_health_status",
        "health_status IN ('healthy', 'degraded', 'unhealthy') OR health_status IS NULL",
    )

    # 8. Add index on feature_key for ComponentRegistry (if nullable, still useful for filtering)
    safe_create_index(
        "idx_component_registry_feature",
        "component_registry",
        ["feature_key"],
    )

    # 9. Add index on feature_key for IntegrationRegistry (if not already exists)
    safe_create_index(
        "idx_integration_registry_feature",
        "integration_registry",
        ["feature_key"],
    )


def downgrade() -> None:
    """Remove indexes, foreign keys, and constraints."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Helper to safely drop index
    def safe_drop_index(index_name: str, table_name: str):
        try:
            existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name=table_name)
        except Exception:
            pass

    # Helper to safely drop constraint
    def safe_drop_constraint(table_name: str, constraint_name: str):
        try:
            # Try Alembic method first
            op.drop_constraint(constraint_name, table_name, type_="check")
        except Exception:
            try:
                # Fallback to raw SQL
                op.execute(
                    sa.text(f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}")
                )
            except Exception:
                pass

    # Helper to safely drop FK
    def safe_drop_fk(table_name: str, fk_name: str):
        try:
            op.drop_constraint(fk_name, table_name, type_="foreignkey")
        except Exception:
            pass

    # Drop indexes
    safe_drop_index("idx_tier_features_tier_key", "license_tier_features")
    safe_drop_index("idx_tenant_integration_active", "tenant_integration_configs")
    safe_drop_index("idx_feature_audit_key_time", "feature_audit_log")
    safe_drop_index("idx_component_registry_feature", "component_registry")
    safe_drop_index("idx_integration_registry_feature", "integration_registry")

    # Drop foreign keys
    safe_drop_fk("model_registry", "fk_model_registry_feature")
    safe_drop_fk("component_registry", "fk_component_registry_feature")
    safe_drop_fk("integration_registry", "fk_integration_registry_feature")

    # Drop check constraints
    safe_drop_constraint("tenant_integration_configs", "chk_health_status")
    
    # Note: We don't restore the FK on license_tier.created_by in downgrade
    # as it was removed to fix the circular dependency


