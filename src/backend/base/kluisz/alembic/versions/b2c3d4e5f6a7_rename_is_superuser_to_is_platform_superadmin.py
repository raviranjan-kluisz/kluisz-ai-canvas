"""Rename is_superuser to is_platform_superadmin

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename is_superuser column to is_platform_superadmin."""
    # Check if the column exists before renaming
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    if 'is_superuser' in columns and 'is_platform_superadmin' not in columns:
        op.alter_column('user', 'is_superuser', new_column_name='is_platform_superadmin')
    elif 'is_platform_superadmin' not in columns:
        # Column doesn't exist at all, add it
        op.add_column('user', sa.Column('is_platform_superadmin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Rename is_platform_superadmin column back to is_superuser."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    if 'is_platform_superadmin' in columns and 'is_superuser' not in columns:
        op.alter_column('user', 'is_platform_superadmin', new_column_name='is_superuser')

