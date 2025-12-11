# Tenant Feature Control - Implementation Plan

## Executive Summary

This document provides a phased implementation plan for the tenant feature control system. The implementation is divided into 5 phases over approximately 4-6 weeks.

---

## Phase 1: Database Foundation (Week 1)

### 1.1 Create Database Models

**Files to create:**
- `src/backend/base/kluisz/services/database/models/feature/model.py`

```python
"""Feature control database models."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from kluisz.schema.serialize import UUIDstr


class FeatureRegistry(SQLModel, table=True):
    """Master registry of all available features."""
    
    __tablename__ = "feature_registry"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    
    # Identification
    feature_key: str = Field(unique=True, index=True)
    feature_name: str
    description: Optional[str] = None
    
    # Categorization
    category: str = Field(index=True)  # models, components, integrations, ui, api, limits
    subcategory: Optional[str] = None
    
    # Feature type and default
    feature_type: str = Field(default="boolean")  # boolean, integer, string, json
    default_value: dict = Field(default_factory=lambda: {"enabled": False}, sa_column=Column(JSON))
    
    # Metadata
    is_premium: bool = Field(default=False)
    requires_setup: bool = Field(default=False)
    depends_on: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    conflicts_with: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # UI hints
    display_order: int = Field(default=0)
    icon: Optional[str] = None
    help_url: Optional[str] = None
    
    # Status
    is_active: bool = Field(default=True, index=True)
    is_deprecated: bool = Field(default=False)
    deprecated_message: Optional[str] = None
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[UUIDstr] = Field(default=None, foreign_key="user.id")


class LicenseTierFeatures(SQLModel, table=True):
    """Features included in each license tier."""
    
    __tablename__ = "license_tier_features"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    
    license_tier_id: UUIDstr = Field(foreign_key="license_tier.id", index=True)
    feature_key: str = Field(foreign_key="feature_registry.feature_key")
    
    # Feature value for this tier
    feature_value: dict = Field(sa_column=Column(JSON))
    
    # Override control
    allow_tenant_override: bool = Field(default=True)
    allow_tenant_upgrade: bool = Field(default=False)
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[UUIDstr] = Field(default=None, foreign_key="user.id")
    
    class Config:
        table_args = {"sqlite_autoincrement": True}


class ModelRegistry(SQLModel, table=True):
    """Registry of available AI models."""
    
    __tablename__ = "model_registry"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    
    # Model identification
    provider: str = Field(index=True)
    model_id: str
    model_name: str
    
    # Categorization
    model_type: str  # chat, completion, embedding, image, audio
    model_family: Optional[str] = None
    
    # Capabilities
    supports_tools: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    supports_streaming: bool = Field(default=True)
    max_tokens: Optional[int] = None
    context_window: Optional[int] = None
    
    # Pricing (per 1K tokens)
    input_price_per_1k: Optional[float] = None
    output_price_per_1k: Optional[float] = None
    
    # Feature key mapping
    feature_key: str = Field(index=True)
    
    # Status
    is_active: bool = Field(default=True, index=True)
    is_deprecated: bool = Field(default=False)
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComponentRegistry(SQLModel, table=True):
    """Registry of available flow components."""
    
    __tablename__ = "component_registry"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    
    # Component identification
    component_key: str = Field(unique=True, index=True)
    component_name: str
    display_name: str
    description: Optional[str] = None
    
    # Categorization
    category: str = Field(index=True)
    subcategory: Optional[str] = None
    
    # Feature key mapping
    feature_key: Optional[str] = None
    
    # Requirements
    required_features: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Metadata
    icon: Optional[str] = None
    documentation_url: Optional[str] = None
    is_beta: bool = Field(default=False)
    
    # Status
    is_active: bool = Field(default=True)
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureAuditLog(SQLModel, table=True):
    """Audit log for feature changes."""
    
    __tablename__ = "feature_audit_log"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    
    # What changed
    entity_type: str  # tenant, tier, registry
    entity_id: UUIDstr
    feature_key: str
    
    # Change details
    action: str  # enable, disable, update, request
    old_value: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    new_value: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Who and when
    performed_by: Optional[UUIDstr] = Field(default=None, foreign_key="user.id")
    performed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
```

### 1.2 Create Migration

**File:** `migrations/versions/xxx_add_feature_control_tables.py`

```python
"""Add feature control tables

Revision ID: xxx
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Feature Registry
    op.create_table(
        'feature_registry',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('feature_key', sa.String(255), nullable=False),
        sa.Column('feature_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('subcategory', sa.String(50), nullable=True),
        sa.Column('feature_type', sa.String(20), nullable=False, server_default='boolean'),
        sa.Column('default_value', sa.JSON(), nullable=False),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_setup', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('depends_on', sa.JSON(), nullable=True),
        sa.Column('conflicts_with', sa.JSON(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('help_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deprecated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deprecated_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_key'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id']),
    )
    op.create_index('idx_feature_registry_category', 'feature_registry', ['category'])
    op.create_index('idx_feature_registry_key', 'feature_registry', ['feature_key'])

    # License Tier Features
    op.create_table(
        'license_tier_features',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('license_tier_id', sa.UUID(), nullable=False),
        sa.Column('feature_key', sa.String(255), nullable=False),
        sa.Column('feature_value', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['license_tier_id'], ['license_tier.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['feature_key'], ['feature_registry.feature_key'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id']),
        sa.UniqueConstraint('license_tier_id', 'feature_key'),
    )
    op.create_index('idx_tier_features_tier', 'license_tier_features', ['license_tier_id'])

    # Model Registry, Component Registry, Audit Log... (similar structure)

def downgrade():
    op.drop_table('license_tier_features')
    op.drop_table('feature_registry')
```

### 1.3 Seed Default Features

**File:** `src/backend/base/kluisz/initial_setup/seed_features.py`

```python
"""Seed default features into the registry."""

from datetime import datetime, timezone
from uuid import uuid4

DEFAULT_FEATURES = [
    # Models - Providers
    {"feature_key": "models.openai", "feature_name": "OpenAI Models", "category": "models", "subcategory": "openai", "default_value": {"enabled": True}},
    {"feature_key": "models.anthropic", "feature_name": "Anthropic Models", "category": "models", "subcategory": "anthropic", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "models.google", "feature_name": "Google AI Models", "category": "models", "subcategory": "google", "default_value": {"enabled": True}},
    {"feature_key": "models.mistral", "feature_name": "Mistral Models", "category": "models", "subcategory": "mistral", "default_value": {"enabled": False}},
    {"feature_key": "models.ollama", "feature_name": "Ollama (Local)", "category": "models", "subcategory": "ollama", "default_value": {"enabled": True}},
    {"feature_key": "models.azure_openai", "feature_name": "Azure OpenAI", "category": "models", "subcategory": "azure", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "models.aws_bedrock", "feature_name": "AWS Bedrock", "category": "models", "subcategory": "aws", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "models.ibm_watsonx", "feature_name": "IBM watsonx.ai", "category": "models", "subcategory": "ibm", "default_value": {"enabled": True}},
    {"feature_key": "models.groq", "feature_name": "Groq", "category": "models", "subcategory": "groq", "default_value": {"enabled": False}},
    {"feature_key": "models.xai", "feature_name": "xAI (Grok)", "category": "models", "subcategory": "xai", "default_value": {"enabled": False}},
    
    # Components - Categories
    {"feature_key": "components.models_and_agents", "feature_name": "Models & Agents", "category": "components", "subcategory": "categories", "default_value": {"enabled": True}},
    {"feature_key": "components.helpers", "feature_name": "Helpers", "category": "components", "subcategory": "categories", "default_value": {"enabled": True}},
    {"feature_key": "components.data_io", "feature_name": "Data I/O", "category": "components", "subcategory": "categories", "default_value": {"enabled": True}},
    {"feature_key": "components.logic", "feature_name": "Logic", "category": "components", "subcategory": "categories", "default_value": {"enabled": True}},
    {"feature_key": "components.embeddings", "feature_name": "Embeddings", "category": "components", "subcategory": "categories", "default_value": {"enabled": True}},
    {"feature_key": "components.memories", "feature_name": "Memories", "category": "components", "subcategory": "categories", "default_value": {"enabled": True}},
    {"feature_key": "components.tools", "feature_name": "Tools", "category": "components", "subcategory": "categories", "default_value": {"enabled": True}},
    {"feature_key": "components.prototypes", "feature_name": "Prototypes (Beta)", "category": "components", "subcategory": "categories", "default_value": {"enabled": False}},
    
    # Components - Custom
    {"feature_key": "components.custom.enabled", "feature_name": "Create Custom Components", "category": "components", "subcategory": "custom", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "components.custom.code_editing", "feature_name": "Edit Component Code", "category": "components", "subcategory": "custom", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "components.custom.import_external", "feature_name": "Import External Components", "category": "components", "subcategory": "custom", "default_value": {"enabled": False}, "is_premium": True},
    
    # Integrations - Observability
    {"feature_key": "integrations.mcp", "feature_name": "MCP Server", "category": "integrations", "subcategory": "observability", "default_value": {"enabled": True}},
    {"feature_key": "integrations.langfuse", "feature_name": "Langfuse", "category": "integrations", "subcategory": "observability", "default_value": {"enabled": False}},
    {"feature_key": "integrations.langsmith", "feature_name": "LangSmith", "category": "integrations", "subcategory": "observability", "default_value": {"enabled": False}},
    {"feature_key": "integrations.langwatch", "feature_name": "LangWatch", "category": "integrations", "subcategory": "observability", "default_value": {"enabled": False}},
    
    # Integrations - Vector Stores
    {"feature_key": "integrations.vector_stores.chroma", "feature_name": "Chroma", "category": "integrations", "subcategory": "vector_stores", "default_value": {"enabled": True}},
    {"feature_key": "integrations.vector_stores.pinecone", "feature_name": "Pinecone", "category": "integrations", "subcategory": "vector_stores", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "integrations.vector_stores.qdrant", "feature_name": "Qdrant", "category": "integrations", "subcategory": "vector_stores", "default_value": {"enabled": False}},
    {"feature_key": "integrations.vector_stores.weaviate", "feature_name": "Weaviate", "category": "integrations", "subcategory": "vector_stores", "default_value": {"enabled": False}},
    
    # UI Features
    {"feature_key": "ui.flow_builder.export_flow", "feature_name": "Export Flow", "category": "ui", "subcategory": "flow_builder", "default_value": {"enabled": True}},
    {"feature_key": "ui.flow_builder.import_flow", "feature_name": "Import Flow", "category": "ui", "subcategory": "flow_builder", "default_value": {"enabled": True}},
    {"feature_key": "ui.flow_builder.share_flow", "feature_name": "Share Flow", "category": "ui", "subcategory": "flow_builder", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "ui.flow_builder.version_control", "feature_name": "Version Control", "category": "ui", "subcategory": "flow_builder", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "ui.code_view.view_code", "feature_name": "View Code", "category": "ui", "subcategory": "code_view", "default_value": {"enabled": True}},
    {"feature_key": "ui.code_view.edit_code", "feature_name": "Edit Code", "category": "ui", "subcategory": "code_view", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "ui.code_view.python_api", "feature_name": "Python API", "category": "ui", "subcategory": "code_view", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "ui.debug.enabled", "feature_name": "Debug Mode", "category": "ui", "subcategory": "debug", "default_value": {"enabled": False}},
    {"feature_key": "ui.debug.step_execution", "feature_name": "Step Execution", "category": "ui", "subcategory": "debug", "default_value": {"enabled": False}},
    {"feature_key": "ui.debug.logs_access", "feature_name": "Logs Access", "category": "ui", "subcategory": "debug", "default_value": {"enabled": True}},
    {"feature_key": "ui.advanced.global_variables", "feature_name": "Global Variables", "category": "ui", "subcategory": "advanced", "default_value": {"enabled": True}},
    {"feature_key": "ui.advanced.api_keys_management", "feature_name": "API Keys Management", "category": "ui", "subcategory": "advanced", "default_value": {"enabled": True}},
    {"feature_key": "ui.advanced.mcp_server_config", "feature_name": "MCP Server Config", "category": "ui", "subcategory": "advanced", "default_value": {"enabled": True}},
    
    # API Features
    {"feature_key": "api.public_endpoints", "feature_name": "Public API Endpoints", "category": "api", "subcategory": "access", "default_value": {"enabled": True}},
    {"feature_key": "api.webhooks", "feature_name": "Webhooks", "category": "api", "subcategory": "access", "default_value": {"enabled": False}, "is_premium": True},
    {"feature_key": "api.streaming_responses", "feature_name": "Streaming Responses", "category": "api", "subcategory": "access", "default_value": {"enabled": True}},
    {"feature_key": "api.batch_execution", "feature_name": "Batch Execution", "category": "api", "subcategory": "access", "default_value": {"enabled": False}, "is_premium": True},
    
    # Limits
    {"feature_key": "limits.max_flows", "feature_name": "Max Flows", "category": "limits", "subcategory": "resources", "feature_type": "integer", "default_value": {"enabled": True, "value": 10}},
    {"feature_key": "limits.max_api_calls_per_month", "feature_name": "Max API Calls/Month", "category": "limits", "subcategory": "resources", "feature_type": "integer", "default_value": {"enabled": True, "value": 1000}},
    {"feature_key": "limits.max_concurrent_executions", "feature_name": "Max Concurrent Executions", "category": "limits", "subcategory": "resources", "feature_type": "integer", "default_value": {"enabled": True, "value": 3}},
    {"feature_key": "limits.max_file_upload_size_mb", "feature_name": "Max File Upload Size (MB)", "category": "limits", "subcategory": "resources", "feature_type": "integer", "default_value": {"enabled": True, "value": 10}},
]

async def seed_feature_registry(session):
    """Seed default features into the registry."""
    from kluisz.services.database.models.feature.model import FeatureRegistry
    from sqlmodel import select
    
    for feature_data in DEFAULT_FEATURES:
        # Check if exists
        stmt = select(FeatureRegistry).where(FeatureRegistry.feature_key == feature_data["feature_key"])
        result = await session.exec(stmt)
        existing = result.first()
        
        if not existing:
            feature = FeatureRegistry(
                id=uuid4(),
                feature_key=feature_data["feature_key"],
                feature_name=feature_data["feature_name"],
                category=feature_data["category"],
                subcategory=feature_data.get("subcategory"),
                feature_type=feature_data.get("feature_type", "boolean"),
                default_value=feature_data["default_value"],
                is_premium=feature_data.get("is_premium", False),
                display_order=DEFAULT_FEATURES.index(feature_data),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(feature)
    
    await session.commit()
```

---

## Phase 2: Backend Service (Week 2)

### Tasks

1. **Create FeatureControlService** (see backend_service.md)
   - Feature resolution with caching
   - Tier feature management
   - Upgrade request workflow

2. **Create API Endpoints**
   - `/api/v2/features` - Get current tenant features
   - `/api/v2/features/check/{key}` - Check specific feature
   - `/api/v2/features/models` - Get enabled models
   - `/api/v2/features/components` - Get enabled components
   - `/api/v2/admin/features/*` - Admin management endpoints

3. **Integrate with existing services**
   - Register FeatureControlService factory
   - Add cache invalidation hooks

---

## Phase 3: Frontend Foundation (Week 3)

### Tasks

1. **Create FeatureContext** (see frontend_gates.md)
   - FeatureProvider component
   - useFeatureFlags hook

2. **Create FeatureGate components**
   - FeatureGate
   - ModelGate
   - IntegrationGate
   - UIFeatureGate

3. **Create API hooks**
   - Feature query hooks
   - Admin mutation hooks

---

## Phase 4: UI Integration (Week 4)

### Tasks

1. **Apply FeatureGate to existing components**
   - Model selectors
   - Component palette
   - Export/Share buttons
   - MCP Server section
   - Integration settings

2. **Create Super Admin UI** (see super_admin_ui.md)
   - TierFeatureBuilder
   - UpgradeRequestsPanel

3. **Add Features tab to Super Admin Page**

---

## Phase 5: Testing & Refinement (Week 5-6)

### Tasks

1. **Backend testing**
   - Unit tests for FeatureControlService
   - Integration tests for API endpoints
   - Cache behavior tests

2. **Frontend testing**
   - Component tests for FeatureGate
   - Hook tests
   - E2E tests for feature gating

3. **Documentation**
   - API documentation
   - Admin user guide
   - Developer guide for adding new features

4. **Performance optimization**
   - Cache tuning
   - Query optimization
   - Frontend bundle analysis

---

## Migration Strategy

### For Existing Tenants

1. Run seed script to populate feature_registry
2. Create default tier features based on existing license_tier.features JSON
3. Assign tenants to appropriate license tiers based on their needs
4. Enable feature control system

### Rollback Plan

1. Feature flag to disable feature control system
2. Fall back to license_tier.features JSON field
3. Database migration rollback scripts

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cache inconsistency | Medium | TTL + manual invalidation |
| Migration data loss | High | Thorough testing + backups |
| Performance regression | Medium | Caching + query optimization |
| User confusion | Low | Clear UI + documentation |

---

## Success Metrics

1. **Functionality**: All features correctly gated
2. **Performance**: Feature resolution < 50ms
3. **Usability**: Admin can configure in < 5 clicks
4. **Reliability**: Zero billing-related bugs




