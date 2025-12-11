"""Seed bundle features into feature registry

Revision ID: e1f2a3b4c5d6
Revises: d8e9f0a1b2c3
Create Date: 2025-01-15 16:00:00.000000

This migration seeds all the bundle features that control external integration
visibility in the sidebar. These features allow tenant-level control over which
integration bundles are available to users.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "d8e9f0a1b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Bundle features to seed
BUNDLE_FEATURES = [
    # AI Provider Bundles
    ("integrations.bundles.openai", "OpenAI Bundle", "bundles_ai", True, False, "OpenAI integration components bundle"),
    ("integrations.bundles.anthropic", "Anthropic Bundle", "bundles_ai", True, False, "Anthropic integration components bundle"),
    ("integrations.bundles.google", "Google Bundle", "bundles_ai", True, False, "Google AI integration components bundle"),
    ("integrations.bundles.mistral", "Mistral Bundle", "bundles_ai", False, True, "Mistral AI integration components bundle"),
    ("integrations.bundles.groq", "Groq Bundle", "bundles_ai", False, True, "Groq inference integration components bundle"),
    ("integrations.bundles.cohere", "Cohere Bundle", "bundles_ai", False, True, "Cohere AI integration components bundle"),
    ("integrations.bundles.huggingface", "HuggingFace Bundle", "bundles_ai", False, True, "HuggingFace integration components bundle"),
    ("integrations.bundles.ollama", "Ollama Bundle", "bundles_ai", True, False, "Ollama local models integration components bundle"),
    ("integrations.bundles.baidu", "Baidu Bundle", "bundles_ai", False, True, "Baidu AI integration components bundle"),
    
    # Cloud Provider Bundles
    ("integrations.bundles.aws", "AWS Bundle", "bundles_cloud", False, True, "AWS integration components bundle (Bedrock, SageMaker)"),
    ("integrations.bundles.azure", "Azure Bundle", "bundles_cloud", False, True, "Azure integration components bundle"),
    ("integrations.bundles.cloudflare", "Cloudflare Bundle", "bundles_cloud", False, True, "Cloudflare integration components bundle"),
    
    # Vector Store & Database Bundles
    ("integrations.bundles.chroma", "Chroma Bundle", "bundles_data", True, False, "Chroma vector store integration components bundle"),
    ("integrations.bundles.pinecone", "Pinecone Bundle", "bundles_data", False, True, "Pinecone vector store integration components bundle"),
    ("integrations.bundles.qdrant", "Qdrant Bundle", "bundles_data", False, True, "Qdrant vector store integration components bundle"),
    ("integrations.bundles.weaviate", "Weaviate Bundle", "bundles_data", False, True, "Weaviate vector store integration components bundle"),
    ("integrations.bundles.milvus", "Milvus Bundle", "bundles_data", False, True, "Milvus vector store integration components bundle"),
    ("integrations.bundles.cassandra", "Cassandra Bundle", "bundles_data", False, True, "Cassandra database integration components bundle"),
    ("integrations.bundles.datastax", "DataStax Bundle", "bundles_data", False, True, "DataStax/Astra DB integration components bundle"),
    ("integrations.bundles.couchbase", "Couchbase Bundle", "bundles_data", False, True, "Couchbase database integration components bundle"),
    ("integrations.bundles.clickhouse", "ClickHouse Bundle", "bundles_data", False, True, "ClickHouse analytics database integration components bundle"),
    
    # Observability Bundles
    # NOTE: Langfuse, LangSmith, and LangWatch are mandatory/always-on for system logging - not feature-gated
    ("integrations.bundles.comet", "Comet Bundle", "bundles_observability", False, True, "Comet ML observability integration components bundle"),
    ("integrations.bundles.cleanlab", "Cleanlab Bundle", "bundles_observability", False, True, "Cleanlab data quality integration components bundle"),
    
    # External Service Bundles
    ("integrations.bundles.notion", "Notion Bundle", "bundles_services", False, True, "Notion integration components bundle"),
    ("integrations.bundles.confluence", "Confluence Bundle", "bundles_services", False, True, "Confluence integration components bundle"),
    ("integrations.bundles.apify", "Apify Bundle", "bundles_services", False, True, "Apify web scraping integration components bundle"),
    ("integrations.bundles.agentql", "AgentQL Bundle", "bundles_services", False, True, "AgentQL integration components bundle"),
    ("integrations.bundles.assemblyai", "AssemblyAI Bundle", "bundles_services", False, True, "AssemblyAI speech-to-text integration components bundle"),
    ("integrations.bundles.composio", "Composio Bundle", "bundles_services", False, True, "Composio integration components bundle"),
    ("integrations.bundles.arxiv", "arXiv Bundle", "bundles_services", True, False, "arXiv research papers integration components bundle"),
    ("integrations.bundles.bing", "Bing Bundle", "bundles_services", False, True, "Bing search integration components bundle"),
    
    # Specialized Bundles
    ("integrations.bundles.altk", "ALTK Bundle", "bundles_specialized", False, True, "ALTK integration components bundle"),
    ("integrations.bundles.cuga", "CUGA Bundle", "bundles_specialized", False, True, "CUGA integration components bundle"),
    ("integrations.bundles.docling", "Docling Bundle", "bundles_specialized", False, True, "Docling document processing integration components bundle"),
]

# UI Features to seed
UI_FEATURES = [
    ("ui.embed.enabled", "Embed Widget", "sharing", False, True, "Embed flow as widget into external sites"),
    ("ui.chat.messages", "Messages", "chat", True, False, "Access to message history and management"),
    ("ui.playground.enabled", "Playground", "testing", True, False, "Access to flow playground for testing"),
    ("ui.templates.enabled", "Templates", "templates", True, False, "Access to flow templates"),
    ("ui.store.enabled", "Component Store", "store", False, True, "Access to component store"),
]


def upgrade() -> None:
    """Seed bundle and UI features into the feature registry."""
    conn = op.get_bind()
    
    # Check if feature_registry table exists
    inspector = sa.inspect(conn)
    if "feature_registry" not in inspector.get_table_names():
        print("feature_registry table does not exist, skipping seed")
        return
    
    now = datetime.now(timezone.utc).isoformat()
    display_order = 100  # Start at 100 to not conflict with existing features
    
    # Seed bundle features
    for feature_key, feature_name, subcategory, enabled, is_premium, description in BUNDLE_FEATURES:
        # Check if feature already exists
        result = conn.execute(
            sa.text("SELECT 1 FROM feature_registry WHERE feature_key = :key"),
            {"key": feature_key}
        )
        if result.fetchone() is None:
            default_value = '{"enabled": ' + str(enabled).lower() + '}'
            conn.execute(
                sa.text("""
                    INSERT INTO feature_registry 
                    (id, feature_key, feature_name, description, category, subcategory, 
                     feature_type, default_value, is_premium, is_active, display_order, created_at, updated_at)
                    VALUES 
                    (:id, :feature_key, :feature_name, :description, :category, :subcategory,
                     :feature_type, :default_value, :is_premium, :is_active, :display_order, :created_at, :updated_at)
                """),
                {
                    "id": str(uuid4()),
                    "feature_key": feature_key,
                    "feature_name": feature_name,
                    "description": description,
                    "category": "integrations",
                    "subcategory": subcategory,
                    "feature_type": "boolean",
                    "default_value": default_value,
                    "is_premium": is_premium,
                    "is_active": True,
                    "display_order": display_order,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            print(f"Seeded feature: {feature_key}")
            display_order += 1
    
    # Seed UI features
    for feature_key, feature_name, subcategory, enabled, is_premium, description in UI_FEATURES:
        # Check if feature already exists
        result = conn.execute(
            sa.text("SELECT 1 FROM feature_registry WHERE feature_key = :key"),
            {"key": feature_key}
        )
        if result.fetchone() is None:
            default_value = '{"enabled": ' + str(enabled).lower() + '}'
            conn.execute(
                sa.text("""
                    INSERT INTO feature_registry 
                    (id, feature_key, feature_name, description, category, subcategory, 
                     feature_type, default_value, is_premium, is_active, display_order, created_at, updated_at)
                    VALUES 
                    (:id, :feature_key, :feature_name, :description, :category, :subcategory,
                     :feature_type, :default_value, :is_premium, :is_active, :display_order, :created_at, :updated_at)
                """),
                {
                    "id": str(uuid4()),
                    "feature_key": feature_key,
                    "feature_name": feature_name,
                    "description": description,
                    "category": "ui",
                    "subcategory": subcategory,
                    "feature_type": "boolean",
                    "default_value": default_value,
                    "is_premium": is_premium,
                    "is_active": True,
                    "display_order": display_order,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            print(f"Seeded feature: {feature_key}")
            display_order += 1
    
    print(f"✅ Seeded bundle and UI features into feature_registry")


def downgrade() -> None:
    """Remove seeded bundle features (optional - usually not done)."""
    conn = op.get_bind()
    
    # Collect all feature keys to potentially remove
    all_feature_keys = [f[0] for f in BUNDLE_FEATURES] + [f[0] for f in UI_FEATURES]
    
    # We don't typically remove seeded data on downgrade
    # But if needed, uncomment this:
    # for feature_key in all_feature_keys:
    #     conn.execute(
    #         sa.text("DELETE FROM feature_registry WHERE feature_key = :key"),
    #         {"key": feature_key}
    #     )
    pass


