# Tenant Feature Control System

## Overview

The Tenant Feature Control System provides granular control over what features, models, components, and integrations are available to each tenant. This enables:

- **Per-tier feature bundling**: Define what each license tier includes
- **License-based access control**: Tenants inherit features from their assigned license tier
- **Model & component gating**: Control which AI models and flow components are available
- **Integration management**: Enable/disable third-party integrations per tier
- **Simple management**: Change tenant features by assigning them to a different tier

---

## Documentation Structure

### 📚 Core Documentation

| Document | Description |
|----------|-------------|
| [architecture.md](./architecture.md) | System architecture, design principles, and feature taxonomy |
| [erd.md](./erd.md) | Complete Entity Relationship Diagram with all relationships |
| [erd-critical-analysis.md](./erd-critical-analysis.md) | Critical analysis, optimizations, and recommended fixes |
| [extensibility-guide.md](./extensibility-guide.md) | Patterns for making the system truly extensible and scalable |

### 🔧 Implementation Guides

| Document | Description |
|----------|-------------|
| [implementation-audit.md](./implementation-audit.md) | Production readiness audit & verification checklist |
| [optimization-implementation.md](./optimization-implementation.md) | Summary of ERD optimizations implemented |
| [implementation_plan.md](./implementation_plan.md) | Phased implementation plan and timeline |

### 💻 Developer Guides

| Document | Description |
|----------|-------------|
| [backend_service.md](./backend_service.md) | Feature Control Service implementation details |
| [frontend_gates.md](./frontend_gates.md) | Frontend feature gating components and hooks |
| [super_admin_ui.md](./super_admin_ui.md) | Super Admin interface for feature management |

### 🔐 Configuration & Security

| Document | Description |
|----------|-------------|
| [tenant-integration-config.md](./tenant-integration-config.md) | Guide to config vs encrypted_config separation for integrations |

---

## Quick Start

### Feature Inheritance Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    GLOBAL FEATURE REGISTRY                       │
│    (All possible features - source of truth)                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ inherits
┌─────────────────────────────▼───────────────────────────────────┐
│                      LICENSE TIER FEATURES                       │
│    (What features each tier includes)                           │
│    Super Admin configures features per tier                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ inherits
┌─────────────────────────────▼───────────────────────────────────┐
│                      USER (via License Tier)                     │
│    Users inherit features from their assigned tier              │
│    To change features: assign user to different tier             │
└─────────────────────────────────────────────────────────────────┘
```

### Feature Categories

| Category | Examples |
|----------|----------|
| **Models** | `models.openai`, `models.anthropic`, `models.google` |
| **Components** | `components.agents`, `components.custom.enabled` |
| **Integrations** | `integrations.mcp`, `integrations.langfuse` |
| **UI** | `ui.flow_builder.export`, `ui.code_view.edit` |
| **API** | `api.webhooks`, `api.batch_execution` |
| **Limits** | `limits.max_flows`, `limits.max_concurrent` |

### Core Database Tables

```sql
feature_registry        -- All available features (source of truth)
license_tier_features   -- What each tier includes
model_registry          -- Available AI models
component_registry      -- Available flow components
integration_registry    -- Available third-party integrations
tenant_integration_configs -- Tenant-specific integration configs
feature_audit_log       -- Change history
```

### API Endpoints

```
GET  /api/v2/features              -- Get user's enabled features
GET  /api/v2/features/models       -- Get enabled models
GET  /api/v2/features/components   -- Get enabled components

PUT  /api/v2/admin/features/tiers/{id}  -- Set tier features
GET  /api/v2/admin/features/tiers/{id}   -- Get tier features
GET  /api/v2/admin/features/registry     -- Get feature registry
```

### Frontend Usage

```tsx
// Feature gate component
<FeatureGate feature="models.anthropic">
  <AnthropicSelector />
</FeatureGate>

// Hook for programmatic checks
const { isFeatureEnabled, enabledModels } = useFeatureFlags();
if (isFeatureEnabled("api.batch_execution")) {
  // ...
}
```

---

## Key Features

### For Super Admins

- **Tier Builder**: Visual interface to configure what each license tier includes
- **Tier Management**: View and edit features for any license tier
- **Tenant Assignment**: Assign tenants to tiers to control their features
- **Audit Log**: Track all feature changes

### For Tenant Admins

- **Features View**: See what features are available based on their tier (read-only)

### For Developers

- **FeatureGate Component**: Declarative feature gating
- **useFeatureFlags Hook**: Programmatic feature checks
- **Type-safe APIs**: Full TypeScript support
- **Centralized Feature Maps**: Metadata-driven gating via `feature-maps.ts`

---

## Architecture Highlights

### Caching Strategy

- Features cached for 5 minutes (configurable)
- Automatic cache invalidation on tier changes
- Redis for distributed deployments, in-memory for single instance

### Performance

- Single query to resolve all features for a user
- Optimized indexes for common query patterns
- Lazy loading of model/component lists

### Security

- Features are controlled exclusively through license tier assignment
- Simple model: assign user to tier = they get tier's features
- Full audit logging of all tier feature changes
- Encrypted storage for sensitive integration credentials

---

## Implementation Status

✅ **Production Ready** - All critical paths implemented and tested

- ✅ Feature registry and tier management
- ✅ Frontend filtering and gating
- ✅ Backend middleware enforcement
- ✅ Flow execution validation
- ✅ ERD optimizations (indexes, constraints)
- ✅ Component metadata enrichment

See [implementation-audit.md](./implementation-audit.md) for complete status.

---

## Related Documentation

- [License Management](../licensing/README.md)
- [Tenant Administration](../tenant-admin/README.md)
- [Super Admin Guide](../super-admin/README.md)

---

## Questions?

Contact the platform team or open an issue in the repository.
