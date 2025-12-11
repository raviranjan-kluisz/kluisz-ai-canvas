"""Add multi-tenant tables

Revision ID: a1b2c3d4e5f6
Revises: a72f5cf9c2f9
Create Date: 2024-12-03 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "a72f5cf9c2f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Helper function to safely create table
    def safe_create_table(table_name, *args, **kwargs):
        if table_name not in existing_tables:
            try:
                op.create_table(table_name, *args, **kwargs)
            except Exception:
                pass  # Table already exists
    
    # Helper function to safely create index
    def safe_create_index(index_name_func, table_name, columns, **kwargs):
        if table_name not in existing_tables:
            return  # Table doesn't exist yet, skip index creation
        try:
            # op.f() returns a callable that generates the index name
            if callable(index_name_func):
                index_name = index_name_func(table_name)
            else:
                index_name = index_name_func
            # Check if index already exists
            existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing_indexes:
                op.create_index(index_name, table_name, columns, **kwargs)
        except Exception as e:
            # Log but don't fail - index might already exist
            pass
    
    # Helper function to safely add column
    def safe_add_column(table_name, column):
        try:
            op.add_column(table_name, column)
        except Exception:
            pass  # Column already exists
    
    # Helper function to safely create foreign key
    def safe_create_fk(fk_name, table_name, ref_table, local_cols, ref_cols, **kwargs):
        try:
            op.create_foreign_key(fk_name, table_name, ref_table, local_cols, ref_cols, **kwargs)
        except Exception:
            pass  # Foreign key already exists
    
    # Create tenant table
    safe_create_table(
        "tenant",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    safe_create_index(op.f("ix_tenant_name"), "tenant", ["name"], unique=False)
    safe_create_index(op.f("ix_tenant_slug"), "tenant", ["slug"], unique=True)
    safe_create_index(op.f("ix_tenant_is_active"), "tenant", ["is_active"], unique=False)

    # Create license table
    safe_create_table(
        "license",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("license_type", sa.String(), nullable=False),
        sa.Column("tier", sa.String(), nullable=False, server_default="basic"),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("max_flows", sa.Integer(), nullable=True),
        sa.Column("max_api_calls", sa.Integer(), nullable=True),
        sa.Column("credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_per_month", sa.Integer(), nullable=True),
        sa.Column("credits_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("billing_cycle", sa.String(), nullable=False, server_default="monthly"),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    safe_create_index(op.f("ix_license_tenant_id"), "license", ["tenant_id"], unique=False)
    safe_create_index(op.f("ix_license_license_type"), "license", ["license_type"], unique=False)
    safe_create_index(op.f("ix_license_tier"), "license", ["tier"], unique=False)
    safe_create_index(op.f("ix_license_is_active"), "license", ["is_active"], unique=False)

    # Create tenant_usage_stats table
    safe_create_table(
        "tenant_usage_stats",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("stats_date", sa.Date(), nullable=False),
        sa.Column("total_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_flows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_flow_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_api_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_storage_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "stats_date", name="uq_tenant_usage_stats_tenant_date"),
    )
    safe_create_index(op.f("ix_tenant_usage_stats_tenant_id"), "tenant_usage_stats", ["tenant_id"], unique=False)
    safe_create_index(op.f("ix_tenant_usage_stats_stats_date"), "tenant_usage_stats", ["stats_date"], unique=False)

    # Create user_usage_stats table
    safe_create_table(
        "user_usage_stats",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("stats_date", sa.Date(), nullable=False),
        sa.Column("flow_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("api_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "stats_date", name="uq_user_usage_stats_user_date"),
    )
    safe_create_index(op.f("ix_user_usage_stats_user_id"), "user_usage_stats", ["user_id"], unique=False)
    safe_create_index(op.f("ix_user_usage_stats_tenant_id"), "user_usage_stats", ["tenant_id"], unique=False)
    safe_create_index(op.f("ix_user_usage_stats_stats_date"), "user_usage_stats", ["stats_date"], unique=False)

    # Add tenant_id and is_tenant_admin to user table
    safe_add_column("user", sa.Column("tenant_id", sa.String(), nullable=True))
    safe_add_column("user", sa.Column("is_tenant_admin", sa.Boolean(), nullable=False, server_default="0"))
    safe_create_fk("fk_user_tenant", "user", "tenant", ["tenant_id"], ["id"], ondelete="SET NULL")
    safe_create_index(op.f("ix_user_tenant_id"), "user", ["tenant_id"], unique=False)

    # Add tenant_id to flow table
    safe_add_column("flow", sa.Column("tenant_id", sa.String(), nullable=True))
    safe_create_fk("fk_flow_tenant", "flow", "tenant", ["tenant_id"], ["id"], ondelete="SET NULL")
    safe_create_index(op.f("ix_flow_tenant_id"), "flow", ["tenant_id"], unique=False)

    # Add tenant_id to folder table
    safe_add_column("folder", sa.Column("tenant_id", sa.String(), nullable=True))
    safe_create_fk("fk_folder_tenant", "folder", "tenant", ["tenant_id"], ["id"], ondelete="SET NULL")
    safe_create_index(op.f("ix_folder_tenant_id"), "folder", ["tenant_id"], unique=False)

    # Add tenant_id to variable table
    safe_add_column("variable", sa.Column("tenant_id", sa.String(), nullable=True))
    safe_create_fk("fk_variable_tenant", "variable", "tenant", ["tenant_id"], ["id"], ondelete="SET NULL")
    safe_create_index(op.f("ix_variable_tenant_id"), "variable", ["tenant_id"], unique=False)

    # Add tenant_id to apikey table
    safe_add_column("apikey", sa.Column("tenant_id", sa.String(), nullable=True))
    safe_create_fk("fk_apikey_tenant", "apikey", "tenant", ["tenant_id"], ["id"], ondelete="SET NULL")
    safe_create_index(op.f("ix_apikey_tenant_id"), "apikey", ["tenant_id"], unique=False)

    # Add tenant_id to file table
    if "file" in existing_tables:
        safe_add_column("file", sa.Column("tenant_id", sa.String(), nullable=True))
        safe_create_fk("fk_file_tenant", "file", "tenant", ["tenant_id"], ["id"], ondelete="SET NULL")
        safe_create_index(op.f("ix_file_tenant_id"), "file", ["tenant_id"], unique=False)


def downgrade() -> None:
    # Remove tenant_id from file table
    op.drop_index(op.f("ix_file_tenant_id"), table_name="file")
    op.drop_constraint("fk_file_tenant", "file", type_="foreignkey")
    op.drop_column("file", "tenant_id")

    # Remove tenant_id from apikey table
    op.drop_index(op.f("ix_apikey_tenant_id"), table_name="apikey")
    op.drop_constraint("fk_apikey_tenant", "apikey", type_="foreignkey")
    op.drop_column("apikey", "tenant_id")

    # Remove tenant_id from variable table
    op.drop_index(op.f("ix_variable_tenant_id"), table_name="variable")
    op.drop_constraint("fk_variable_tenant", "variable", type_="foreignkey")
    op.drop_column("variable", "tenant_id")

    # Remove tenant_id from folder table
    op.drop_index(op.f("ix_folder_tenant_id"), table_name="folder")
    op.drop_constraint("fk_folder_tenant", "folder", type_="foreignkey")
    op.drop_column("folder", "tenant_id")

    # Remove tenant_id from flow table
    op.drop_index(op.f("ix_flow_tenant_id"), table_name="flow")
    op.drop_constraint("fk_flow_tenant", "flow", type_="foreignkey")
    op.drop_column("flow", "tenant_id")

    # Remove tenant_id and is_tenant_admin from user table
    op.drop_index(op.f("ix_user_tenant_id"), table_name="user")
    op.drop_constraint("fk_user_tenant", "user", type_="foreignkey")
    op.drop_column("user", "is_tenant_admin")
    op.drop_column("user", "tenant_id")

    # Drop user_usage_stats table
    op.drop_index(op.f("ix_user_usage_stats_stats_date"), table_name="user_usage_stats")
    op.drop_index(op.f("ix_user_usage_stats_tenant_id"), table_name="user_usage_stats")
    op.drop_index(op.f("ix_user_usage_stats_user_id"), table_name="user_usage_stats")
    op.drop_table("user_usage_stats")

    # Drop tenant_usage_stats table
    op.drop_index(op.f("ix_tenant_usage_stats_stats_date"), table_name="tenant_usage_stats")
    op.drop_index(op.f("ix_tenant_usage_stats_tenant_id"), table_name="tenant_usage_stats")
    op.drop_table("tenant_usage_stats")

    # Drop license table
    op.drop_index(op.f("ix_license_is_active"), table_name="license")
    op.drop_index(op.f("ix_license_tier"), table_name="license")
    op.drop_index(op.f("ix_license_license_type"), table_name="license")
    op.drop_index(op.f("ix_license_tenant_id"), table_name="license")
    op.drop_table("license")

    # Drop tenant table
    op.drop_index(op.f("ix_tenant_is_active"), table_name="tenant")
    op.drop_index(op.f("ix_tenant_slug"), table_name="tenant")
    op.drop_index(op.f("ix_tenant_name"), table_name="tenant")
    op.drop_table("tenant")

