# Tenant Feature Control System - Architecture

## Executive Summary

This document outlines a comprehensive feature control system that allows granular control over what features, models, components, and integrations are available. Features are defined at the **license tier level**, and **users inherit features from their assigned license tier** (via `user.license_tier_id`). This provides a simple, predictable model where feature access is controlled through license tier assignment to individual users.

**Current Implementation**: The system uses a license-based model where:
- Super Admin creates license pools for tenants (stored in `tenant.license_pools` JSON)
- Tenant Admin assigns licenses from pools to users
- Users have `license_tier_id` directly (FK to `license_tier`)
- Features are checked per user based on their `license_tier_id`

---

## 1. Core Principles

### 1.1 Feature Inheritance Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    GLOBAL FEATURE REGISTRY                       │
│    (All possible features defined here - source of truth)       │
│    Default: all features disabled unless explicitly enabled     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ inherits
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LICENSE TIER FEATURES                       │
│    (What features a tier includes - e.g., "Enterprise" tier)    │
│    Super Admin configures which features each tier includes      │
└─────────────────────────────┬───────────────────────────────────┘
                              │ inherits
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USER (via License Tier)                      │
│    Users inherit features from their assigned license_tier_id    │
│    To change features: assign user to different license tier     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Feature Control Rules

| Level | Can Enable | Can Disable | Scope |
|-------|-----------|-------------|-------|
| Global Registry | ✅ Define all | ✅ Set defaults | Platform-wide |
| License Tier | ✅ Enable from registry | ❌ N/A | All users with this tier |
| User | ❌ N/A | ❌ N/A | Inherits from assigned tier |

**Key Principle**: Features are controlled exclusively through license tier assignment to users. To change a user's features, assign them to a different license tier via `user.license_tier_id`.

---

## 2. Feature Categories & Taxonomy

### 2.1 Feature Key Structure

```
category.subcategory.item.variant
```

Examples:
- `models.openai.gpt4.turbo`
- `components.agents.tool_calling`
- `integrations.mcp.enabled`
- `ui.flow_builder.export`

### 2.2 Complete Feature Taxonomy

```yaml
# MODELS - LLM Provider & Model Access
models:
  openai:
    enabled: true/false        # Provider-level toggle
    models:                    # Specific model access
      - gpt-4
      - gpt-4-turbo
      - gpt-4o
      - gpt-4o-mini
      - gpt-3.5-turbo
      - o1-preview
      - o1-mini
  anthropic:
    enabled: true/false
    models:
      - claude-3-opus
      - claude-3-sonnet
      - claude-3-haiku
      - claude-3.5-sonnet
      - claude-3.5-haiku
  google:
    enabled: true/false
    models:
      - gemini-pro
      - gemini-1.5-pro
      - gemini-1.5-flash
  mistral:
    enabled: true/false
    models:
      - mistral-large
      - mistral-medium
      - mistral-small
  ollama:
    enabled: true/false
    base_url_allowed: true/false  # Can configure custom Ollama
  azure_openai:
    enabled: true/false
  aws_bedrock:
    enabled: true/false
  ibm_watsonx:
    enabled: true/false
  groq:
    enabled: true/false
  xai:
    enabled: true/false

# COMPONENTS - Flow Builder Blocks
components:
  categories:
    models_and_agents: true/false
    helpers: true/false
    data_io: true/false
    logic: true/false
    embeddings: true/false
    memories: true/false
    tools: true/false
    prototypes: true/false
  specific:
    agent_component: true/false
    rag_component: true/false
    memory_component: true/false
  custom_components:
    enabled: true/false          # Can create custom components
    code_editing: true/false     # Can edit component code
    import_external: true/false  # Can import from external sources

# INTEGRATIONS - Third-party Services
integrations:
  mcp:
    enabled: true/false
    max_servers: 5               # Limit on MCP servers
  langfuse:
    enabled: true/false
  langsmith:
    enabled: true/false
  langwatch:
    enabled: true/false
  vector_stores:
    chroma: true/false
    pinecone: true/false
    qdrant: true/false
    weaviate: true/false
    milvus: true/false
  databases:
    postgres: true/false
    mongodb: true/false
    airtable: true/false
    notion: true/false

# UI - User Interface Features
ui:
  flow_builder:
    enabled: true/false
    export_flow: true/false
    import_flow: true/false
    share_flow: true/false
    duplicate_flow: true/false
    version_control: true/false
  code_view:
    view_code: true/false
    edit_code: true/false
    python_api: true/false
  playground:
    enabled: true/false
    streaming: true/false
  debug:
    enabled: true/false
    step_execution: true/false
    logs_access: true/false
  advanced:
    global_variables: true/false
    api_keys_management: true/false
    mcp_server_config: true/false

# API - API & External Access
api:
  public_endpoints: true/false
  webhooks: true/false
  rate_limit_override: null     # null = tier default, number = custom
  streaming_responses: true/false
  batch_execution: true/false

# LIMITS - Resource Limits (overrides tier defaults)
limits:
  max_flows: null               # null = tier default
  max_api_calls_per_month: null
  max_concurrent_executions: null
  max_tokens_per_request: null
  max_file_upload_size_mb: null
```

---

## 3. Database Schema

The system uses a normalized database schema with the following key tables:

- **`feature_registry`**: Master registry of all available features (source of truth)
- **`license_tier_features`**: Features assigned to each license tier
- **`model_registry`**: Available AI models mapped to features
- **`component_registry`**: Available flow components mapped to features
- **`integration_registry`**: Available third-party integrations mapped to features
- **`tenant_integration_configs`**: Tenant-specific integration configurations
- **`feature_audit_log`**: Audit trail of all feature changes

For complete ERD diagrams, table definitions, relationships, indexes, and constraints, see [erd.md](./erd.md).

---

## 5. Related Documentation

For detailed implementation guides, see:

- [erd.md](./erd.md) - Complete ERD with all relationships and diagrams
- [erd-critical-analysis.md](./erd-critical-analysis.md) - Database optimization analysis
- [backend_service.md](./backend_service.md) - Feature Control Service implementation
- [super_admin_ui.md](./super_admin_ui.md) - Super Admin interface design
- [frontend_gates.md](./frontend_gates.md) - Frontend feature gating
- [extensibility-guide.md](./extensibility-guide.md) - Making the system extensible



