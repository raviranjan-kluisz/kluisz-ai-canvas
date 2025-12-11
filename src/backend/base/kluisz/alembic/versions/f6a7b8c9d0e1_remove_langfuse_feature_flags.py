"""Remove all observability feature flags - observability is mandatory/always-on

Revision ID: f6a7b8c9d0e1
Revises: e1f2a3b4c5d6
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove all observability feature entries - they are mandatory/always-on for system logging."""
    
    conn = op.get_bind()
    
    # Remove all observability feature flags from feature_registry
    # Langfuse, LangSmith, and LangWatch are all mandatory for system logging
    observability_keys = [
        'integrations.langfuse',
        'integrations.langsmith',
        'integrations.langwatch',
        'integrations.bundles.langfuse',
        'integrations.bundles.langsmith',
        'integrations.bundles.langwatch'
    ]
    
    for key in observability_keys:
        conn.execute(
            sa.text("DELETE FROM feature_registry WHERE feature_key = :key"),
            {"key": key}
        )
        conn.execute(
            sa.text("DELETE FROM license_tier_features WHERE feature_key = :key"),
            {"key": key}
        )


def downgrade() -> None:
    """Re-add observability feature entries if needed."""
    
    # Re-add integrations.langfuse
    op.execute("""
        INSERT INTO feature_registry (
            feature_key, feature_name, description, category, subcategory,
            feature_type, default_value, is_premium, is_active
        ) VALUES 
        ('integrations.langfuse', 'Langfuse', 'Langfuse observability integration', 
         'integrations', 'observability', 'boolean', '{"enabled": false}', true, true),
        ('integrations.langsmith', 'LangSmith', 'LangSmith observability integration', 
         'integrations', 'observability', 'boolean', '{"enabled": false}', true, true),
        ('integrations.langwatch', 'LangWatch', 'LangWatch observability integration', 
         'integrations', 'observability', 'boolean', '{"enabled": false}', true, true),
        ('integrations.bundles.langfuse', 'Langfuse Bundle', 'Langfuse observability bundle', 
         'integrations', 'bundles_observability', 'boolean', '{"enabled": false}', true, true),
        ('integrations.bundles.langsmith', 'LangSmith Bundle', 'LangSmith observability bundle', 
         'integrations', 'bundles_observability', 'boolean', '{"enabled": false}', true, true),
        ('integrations.bundles.langwatch', 'LangWatch Bundle', 'LangWatch observability bundle', 
         'integrations', 'bundles_observability', 'boolean', '{"enabled": false}', true, true)
        ON CONFLICT (feature_key) DO NOTHING
    """)


