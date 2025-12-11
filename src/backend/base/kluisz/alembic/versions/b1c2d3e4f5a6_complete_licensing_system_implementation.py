"""Complete licensing system implementation

Revision ID: b1c2d3e4f5a6
Revises: b2c3d4e5f6a7
Create Date: 2024-12-04 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "b2c3d4e5f6a7"
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
    
    def safe_add_column(table_name, column):
        try:
            op.add_column(table_name, column)
        except Exception:
            pass
    
    def safe_create_index(index_name, table_name, columns, **kwargs):
        try:
            existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing_indexes:
                op.create_index(index_name, table_name, columns, **kwargs)
        except Exception:
            pass
    
    def safe_drop_table(table_name):
        if table_name in existing_tables:
            try:
                op.drop_table(table_name)
            except Exception:
                pass
    
    # 1. Create license_tier table
    safe_create_table(
        "license_tier",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("token_price_per_1000", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("credits_per_usd", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("pricing_multiplier", sa.Numeric(precision=10, scale=2), nullable=False, server_default="1.00"),
        sa.Column("default_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("default_credits_per_month", sa.Integer(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("max_flows", sa.Integer(), nullable=True),
        sa.Column("max_api_calls", sa.Integer(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    safe_create_index("ix_license_tier_name", "license_tier", ["name"], unique=True)
    safe_create_index("ix_license_tier_is_active", "license_tier", ["is_active"], unique=False)
    
    # 2. Create subscription table
    safe_create_table(
        "subscription",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("tier_id", sa.String(), nullable=True),
        sa.Column("license_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monthly_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("billing_cycle", sa.String(), nullable=False, server_default="monthly"),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("renewal_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_method_id", sa.String(), nullable=True),
        sa.Column("last_payment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_payment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["tier_id"], ["license_tier.id"]),
    )
    safe_create_index("ix_subscription_tenant_id", "subscription", ["tenant_id"], unique=False)
    safe_create_index("ix_subscription_status", "subscription", ["status"], unique=False)
    safe_create_index("ix_subscription_renewal_date", "subscription", ["renewal_date"], unique=False)
    safe_create_index("ix_subscription_next_payment_date", "subscription", ["next_payment_date"], unique=False)
    
    # 3. Create subscription_history table
    safe_create_table(
        "subscription_history",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("subscription_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("old_tier_id", sa.String(), nullable=True),
        sa.Column("new_tier_id", sa.String(), nullable=True),
        sa.Column("old_license_count", sa.Integer(), nullable=True),
        sa.Column("new_license_count", sa.Integer(), nullable=True),
        sa.Column("old_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("new_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscription.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["user.id"]),
    )
    safe_create_index("ix_subscription_history_subscription_id", "subscription_history", ["subscription_id"], unique=False)
    safe_create_index("ix_subscription_history_tenant_id", "subscription_history", ["tenant_id"], unique=False)
    safe_create_index("ix_subscription_history_action", "subscription_history", ["action"], unique=False)
    
    # 4. Add license fields to user table
    if "user" in existing_tables:
        safe_add_column("user", sa.Column("license_pool_id", sa.String(), nullable=True))
        safe_add_column("user", sa.Column("license_tier_id", sa.String(), nullable=True))
        safe_add_column("user", sa.Column("credits_allocated", sa.Integer(), nullable=False, server_default="0"))
        safe_add_column("user", sa.Column("credits_used", sa.Integer(), nullable=False, server_default="0"))
        safe_add_column("user", sa.Column("credits_per_month", sa.Integer(), nullable=True))
        safe_add_column("user", sa.Column("license_assigned_at", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("user", sa.Column("license_assigned_by", sa.String(), nullable=True))
        safe_add_column("user", sa.Column("license_expires_at", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("user", sa.Column("license_is_active", sa.Boolean(), nullable=False, server_default="0"))
        
        safe_create_index("ix_user_license_pool_id", "user", ["license_pool_id"], unique=False)
        safe_create_index("ix_user_license_tier_id", "user", ["license_tier_id"], unique=False)
        safe_create_index("ix_user_license_is_active", "user", ["license_is_active"], unique=False)
        
        # Add foreign keys
        try:
            op.create_foreign_key("fk_user_license_tier_id", "user", "license_tier", ["license_tier_id"], ["id"])
        except Exception:
            pass
        try:
            op.create_foreign_key("fk_user_license_assigned_by", "user", "user", ["license_assigned_by"], ["id"])
        except Exception:
            pass
    
    # 5. Add license_pools JSON and subscription fields to tenant table
    if "tenant" in existing_tables:
        safe_add_column("tenant", sa.Column("license_pools", sa.JSON(), nullable=True, server_default="{}"))
        safe_add_column("tenant", sa.Column("subscription_tier_id", sa.String(), nullable=True))
        safe_add_column("tenant", sa.Column("subscription_license_count", sa.Integer(), nullable=False, server_default="0"))
        safe_add_column("tenant", sa.Column("subscription_status", sa.String(), nullable=True))
        safe_add_column("tenant", sa.Column("subscription_start_date", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("tenant", sa.Column("subscription_end_date", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("tenant", sa.Column("subscription_renewal_date", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("tenant", sa.Column("subscription_payment_method_id", sa.String(), nullable=True))
        safe_add_column("tenant", sa.Column("subscription_amount", sa.Numeric(precision=10, scale=2), nullable=True))
        safe_add_column("tenant", sa.Column("subscription_currency", sa.String(), nullable=False, server_default="USD"))
        
        safe_create_index("ix_tenant_subscription_tier_id", "tenant", ["subscription_tier_id"], unique=False)
        safe_create_index("ix_tenant_subscription_status", "tenant", ["subscription_status"], unique=False)
        safe_create_index("ix_tenant_subscription_renewal_date", "tenant", ["subscription_renewal_date"], unique=False)
        
        # Add foreign key
        try:
            op.create_foreign_key("fk_tenant_subscription_tier_id", "tenant", "license_tier", ["subscription_tier_id"], ["id"])
        except Exception:
            pass
    
    # 6. Add credit transaction fields to transaction table
    if "transaction" in existing_tables:
        safe_add_column("transaction", sa.Column("user_id", sa.String(), nullable=True))
        safe_add_column("transaction", sa.Column("transaction_type", sa.String(), nullable=True))
        safe_add_column("transaction", sa.Column("credits_amount", sa.Integer(), nullable=True))
        safe_add_column("transaction", sa.Column("credits_before", sa.Integer(), nullable=True))
        safe_add_column("transaction", sa.Column("credits_after", sa.Integer(), nullable=True))
        safe_add_column("transaction", sa.Column("usage_record_id", sa.String(), nullable=True))
        safe_add_column("transaction", sa.Column("transaction_metadata", sa.JSON(), nullable=True))
        safe_add_column("transaction", sa.Column("created_by", sa.String(), nullable=True))
        
        safe_create_index("ix_transaction_user_id", "transaction", ["user_id"], unique=False)
        safe_create_index("ix_transaction_transaction_type", "transaction", ["transaction_type"], unique=False)
        
        # Make existing fields nullable for credit transactions
        try:
            op.alter_column("transaction", "vertex_id", nullable=True)
            op.alter_column("transaction", "status", nullable=True)
            op.alter_column("transaction", "flow_id", nullable=True)
        except Exception:
            pass
        
        # Add foreign keys
        try:
            op.create_foreign_key("fk_transaction_user_id", "transaction", "user", ["user_id"], ["id"])
        except Exception:
            pass
        try:
            op.create_foreign_key("fk_transaction_created_by", "transaction", "user", ["created_by"], ["id"])
        except Exception:
            pass
    
    # 7. Update tenant_usage_stats table
    if "tenant_usage_stats" in existing_tables:
        # Drop old unique constraint if exists
        try:
            op.drop_constraint("uq_tenant_usage_stats_tenant_date", "tenant_usage_stats", type_="unique")
        except Exception:
            pass
        
        # Add new columns
        safe_add_column("tenant_usage_stats", sa.Column("period_start", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("tenant_usage_stats", sa.Column("period_end", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("tenant_usage_stats", sa.Column("total_credits_used", sa.Integer(), nullable=False, server_default="0"))
        safe_add_column("tenant_usage_stats", sa.Column("total_traces", sa.Integer(), nullable=False, server_default="0"))
        safe_add_column("tenant_usage_stats", sa.Column("total_cost_usd", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"))
        safe_add_column("tenant_usage_stats", sa.Column("active_users_count", sa.Integer(), nullable=False, server_default="0"))
        
        # Migrate data: convert stats_date to period_start/period_end
        try:
            conn.execute(sa.text("""
                UPDATE tenant_usage_stats 
                SET period_start = datetime(stats_date || ' 00:00:00'),
                    period_end = datetime(stats_date || ' 23:59:59')
                WHERE period_start IS NULL
            """))
        except Exception:
            pass
        
        # Create new unique constraint
        try:
            op.create_unique_constraint("uq_tenant_usage_stats_tenant_period", "tenant_usage_stats", ["tenant_id", "period_start", "period_end"])
        except Exception:
            pass
        
        safe_create_index("ix_tenant_usage_stats_period", "tenant_usage_stats", ["period_start", "period_end"], unique=False)
    
    # 8. Update user_usage_stats table
    if "user_usage_stats" in existing_tables:
        # Drop old unique constraint if exists
        try:
            op.drop_constraint("uq_user_usage_stats_user_date", "user_usage_stats", type_="unique")
        except Exception:
            pass
        
        # Add new columns
        safe_add_column("user_usage_stats", sa.Column("period_start", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("user_usage_stats", sa.Column("period_end", sa.DateTime(timezone=True), nullable=True))
        safe_add_column("user_usage_stats", sa.Column("traces_count", sa.Integer(), nullable=False, server_default="0"))
        safe_add_column("user_usage_stats", sa.Column("cost_usd", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"))
        
        # Migrate data: convert stats_date to period_start/period_end
        try:
            conn.execute(sa.text("""
                UPDATE user_usage_stats 
                SET period_start = datetime(stats_date || ' 00:00:00'),
                    period_end = datetime(stats_date || ' 23:59:59')
                WHERE period_start IS NULL
            """))
        except Exception:
            pass
        
        # Create new unique constraint
        try:
            op.create_unique_constraint("uq_user_usage_stats_user_period", "user_usage_stats", ["user_id", "period_start", "period_end"])
        except Exception:
            pass
        
        safe_create_index("ix_user_usage_stats_period", "user_usage_stats", ["period_start", "period_end"], unique=False)
    
    # 9. Drop old redundant tables (if they exist)
    safe_drop_table("user_license")
    safe_drop_table("license_pool")
    safe_drop_table("credit_transaction")
    # Note: license table is disabled (table=False) but not dropped for backward compatibility


def downgrade() -> None:
    # Reverse operations
    op.drop_table("subscription_history")
    op.drop_table("subscription")
    op.drop_table("license_tier")
    
    # Remove columns from user table
    try:
        op.drop_column("user", "license_pool_id")
        op.drop_column("user", "license_tier_id")
        op.drop_column("user", "credits_allocated")
        op.drop_column("user", "credits_used")
        op.drop_column("user", "credits_per_month")
        op.drop_column("user", "license_assigned_at")
        op.drop_column("user", "license_assigned_by")
        op.drop_column("user", "license_expires_at")
        op.drop_column("user", "license_is_active")
    except Exception:
        pass
    
    # Remove columns from tenant table
    try:
        op.drop_column("tenant", "license_pools")
        op.drop_column("tenant", "subscription_tier_id")
        op.drop_column("tenant", "subscription_license_count")
        op.drop_column("tenant", "subscription_status")
        op.drop_column("tenant", "subscription_start_date")
        op.drop_column("tenant", "subscription_end_date")
        op.drop_column("tenant", "subscription_renewal_date")
        op.drop_column("tenant", "subscription_payment_method_id")
        op.drop_column("tenant", "subscription_amount")
        op.drop_column("tenant", "subscription_currency")
    except Exception:
        pass
    
    # Remove columns from transaction table
    try:
        op.drop_column("transaction", "user_id")
        op.drop_column("transaction", "transaction_type")
        op.drop_column("transaction", "credits_amount")
        op.drop_column("transaction", "credits_before")
        op.drop_column("transaction", "credits_after")
        op.drop_column("transaction", "usage_record_id")
        op.drop_column("transaction", "transaction_metadata")
        op.drop_column("transaction", "created_by")
    except Exception:
        pass

