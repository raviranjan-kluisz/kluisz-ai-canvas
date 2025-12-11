# Feature Control System Guide

This guide explains the Kluisz Kanvas Feature Control System - how features are defined, controlled, and enforced across the platform.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Feature Registry](#feature-registry)
4. [License Tiers](#license-tiers)
5. [Feature Resolution](#feature-resolution)
6. [Frontend Integration](#frontend-integration)
7. [Backend Enforcement](#backend-enforcement)
8. [Administration](#administration)
9. [Best Practices](#best-practices)

---

## Overview

The Feature Control System enables:
- **Multi-tenant licensing**: Different tenants get different feature sets
- **Tiered access**: Basic, Pro, Enterprise tiers with different capabilities
- **Granular control**: Enable/disable specific integrations, models, UI features
- **Centralized management**: Super Admin UI for configuration

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Feature** | A controllable capability (e.g., "OpenAI models access") |
| **Feature Key** | Unique identifier (e.g., `models.openai`) |
| **License Tier** | A bundle of features (e.g., "Basic", "Pro") |
| **Tenant** | An organization using the platform |
| **License Pool** | Available licenses of each tier for a tenant |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Feature Registry                         │
│  (Database: feature_registry table)                         │
│  - All available features defined here                      │
│  - Default values, categories, descriptions                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     License Tiers                            │
│  (Database: license_tier + license_tier_features tables)    │
│  - Tiers: Basic, Pro, Enterprise                            │
│  - Each tier has specific features enabled/disabled         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Tenant License Pools                     │
│  (Database: tenant.license_pools JSON field)                │
│  - How many licenses of each tier a tenant has              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     User License Assignment                  │
│  (Database: user.license_tier_id)                           │
│  - Each user assigned to one tier                           │
│  - User inherits tier's features                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Feature Resolution                       │
│  (Runtime: FeatureControlService)                           │
│  - Resolves user's effective features                       │
│  - Caches results for performance                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Feature Registry

### Database Schema

```sql
CREATE TABLE feature_registry (
    id UUID PRIMARY KEY,
    feature_key VARCHAR(255) UNIQUE NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    feature_type VARCHAR(20) DEFAULT 'boolean',
    default_value JSONB NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    depends_on TEXT[],
    display_order INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Feature Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `models` | LLM provider access | `models.openai`, `models.anthropic` |
| `components` | Flow builder components | `components.custom.enabled` |
| `integrations` | External integrations | `integrations.mcp`, `integrations.bundles.openai` |
| `ui` | UI features | `ui.flow_builder.export_flow` |
| `api` | API access | `api.webhooks`, `api.batch_execution` |
| `limits` | Resource limits | `limits.max_flows`, `limits.max_api_calls` |

### Feature Key Convention

```
category.subcategory.item
```

Examples:
- `models.openai` - OpenAI model access
- `integrations.bundles.mongodb` - MongoDB bundle visibility
- `ui.flow_builder.export_flow` - Export flow feature
- `limits.max_flows` - Maximum flows limit

### Adding Features (Backend)

```python
# src/backend/base/kluisz/initial_setup/seed_features.py

DEFAULT_FEATURES = [
    {
        "feature_key": "my_category.my_feature",
        "feature_name": "My Feature",
        "category": "my_category",
        "subcategory": "subcategory",
        "default_value": {"enabled": False},
        "is_premium": True,
        "description": "Description of the feature",
    },
]
```

---

## License Tiers

### Database Schema

```sql
CREATE TABLE license_tier (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    default_credits INTEGER DEFAULT 0,
    default_credits_per_month INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE license_tier_features (
    id UUID PRIMARY KEY,
    license_tier_id UUID REFERENCES license_tier(id),
    feature_key VARCHAR(255) NOT NULL,
    feature_value JSONB NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(license_tier_id, feature_key)
);
```

### Example Tier Configuration

```
Basic Tier:
├── models.openai: enabled
├── models.anthropic: enabled
├── models.google: enabled
├── models.mistral: disabled
├── integrations.bundles.openai: enabled
├── integrations.bundles.chroma: enabled
├── integrations.bundles.pinecone: disabled
├── ui.flow_builder.export_flow: enabled
├── api.webhooks: disabled
└── limits.max_flows: 10

Pro Tier:
├── models.*: enabled
├── integrations.bundles.*: enabled
├── ui.*: enabled
├── api.*: enabled
└── limits.max_flows: 100

Enterprise Tier:
├── *: enabled (all features)
└── limits.max_flows: unlimited
```

---

## Feature Resolution

### Resolution Order

1. **Global Defaults** - From `feature_registry.default_value`
2. **Tier Override** - From `license_tier_features.feature_value`
3. **User Assignment** - User inherits from assigned tier

### FeatureControlService

```python
# src/backend/base/kluisz/services/features/control_service.py

class FeatureControlService:
    async def get_user_features(self, user_id: str) -> dict:
        """
        Get all resolved features for a user.
        
        Returns:
            {
                "features": {
                    "models.openai": {"enabled": True, "source": "tier"},
                    "api.webhooks": {"enabled": False, "source": "default"},
                },
                "tier_id": "uuid",
                "tier_name": "Basic",
                "computed_at": "2024-01-01T00:00:00Z"
            }
        """
        
    async def is_feature_enabled(self, user_id: str, feature_key: str) -> bool:
        """Quick check if a specific feature is enabled."""
```

### Caching

- Features are cached for 5 minutes per user
- Cache key: `features:user:{user_id}`
- Cache invalidated when tier features change

---

## Frontend Integration

### Feature Context

```typescript
// src/frontend/src/contexts/featureContext.tsx

export function useFeatureFlags() {
  return {
    isFeatureEnabled: (featureKey: string) => boolean,
    getFeatureValue: <T>(featureKey: string) => T | null,
    enabledModels: EnabledModel[],
    enabledModelProviders: string[],
    enabledComponents: string[],
    tierName: string | null,
    tierId: string | null,
    isLoading: boolean,
    error: Error | null,
    refetch: () => void,
  };
}
```

### Using in Components

```tsx
import { useFeatureFlags } from "@/contexts/featureContext";

function MyComponent() {
  const { isFeatureEnabled } = useFeatureFlags();
  
  if (!isFeatureEnabled("my.feature.key")) {
    return null; // Or show upgrade prompt
  }
  
  return <div>Feature content</div>;
}
```

### Feature Gate Component

```tsx
import { FeatureGate } from "@/components/FeatureGate";

function App() {
  return (
    <FeatureGate feature="api.webhooks" fallback={<UpgradePrompt />}>
      <WebhookSettings />
    </FeatureGate>
  );
}
```

### Feature Maps

```typescript
// src/frontend/src/constants/feature-maps.ts

// Bundle visibility
export const BUNDLE_FEATURES: Record<string, string> = {
  OpenAI: "integrations.bundles.openai",
  MongoDB: "integrations.bundles.mongodb",
};

// Settings sidebar visibility
export const SETTINGS_SIDEBAR_FEATURES: Record<string, string[]> = {
  "mcp-servers": ["integrations.mcp"],
  "api-keys": ["ui.advanced.api_keys_management"],
};

// Toolbar actions
export const FLOW_TOOLBAR_FEATURES: Record<string, string[]> = {
  export: ["ui.flow_builder.export_flow"],
  webhook: ["api.webhooks"],
};
```

---

## Backend Enforcement

### Route Middleware

```python
# Automatic protection based on route patterns
# src/backend/base/kluisz/api/middleware/feature_middleware.py

ROUTE_FEATURE_MAP = {
    r"/api/v[12]/mcp/.*": ["integrations.mcp"],
    r"/api/v[12]/webhooks.*": ["api.webhooks"],
    r"/api/v[12]/custom-components.*": ["components.custom.enabled"],
}

class FeatureEnforcementMiddleware:
    async def dispatch(self, request, call_next):
        # Check if route requires features
        # Deny if user doesn't have required features
```

### Decorator Protection

```python
from kluisz.api.decorators import require_feature

@router.post("/webhooks")
@require_feature("api.webhooks")
async def create_webhook(current_user: User):
    # Only accessible if user has api.webhooks feature
    pass
```

### Service-Level Check

```python
from kluisz.services.features.control_service import FeatureControlService

async def execute_flow(user_id: str, flow_id: str):
    service = FeatureControlService()
    
    # Check streaming feature
    if streaming_enabled:
        if not await service.is_feature_enabled(user_id, "api.streaming_responses"):
            raise FeatureNotEnabled("Streaming not available in your plan")
    
    # Check model access
    if not await service.is_feature_enabled(user_id, f"models.{model_provider}"):
        raise FeatureNotEnabled(f"{model_provider} not available in your plan")
```

---

## Administration

### Super Admin UI

The Super Admin can:
1. **Create License Tiers** - Define new tiers with pricing
2. **Configure Tier Features** - Enable/disable features per tier
3. **View Feature Registry** - See all available features
4. **Manage Tenant Pools** - Allocate licenses to tenants

### API Endpoints

```
# Feature management (Super Admin)
GET  /api/v2/features/admin/registry     # List all features
GET  /api/v2/features/admin/tiers/{id}   # Get tier features
PUT  /api/v2/features/admin/tiers/{id}   # Update tier features

# User features (Any authenticated user)
GET  /api/v2/features                    # Get my features
GET  /api/v2/features/check/{key}        # Check specific feature
GET  /api/v2/features/models             # Get enabled models
GET  /api/v2/features/components         # Get enabled components

# License assignment (Tenant Admin)
POST /api/v2/admin/user-licenses/assign
POST /api/v2/admin/user-licenses/unassign
POST /api/v2/admin/user-licenses/upgrade
```

### Tenant Admin UI

The Tenant Admin can:
1. **View License Pool** - See available licenses
2. **Assign Licenses** - Assign users to tiers
3. **Upgrade/Downgrade** - Change user tiers
4. **View Usage** - See credits and usage

---

## Best Practices

### Feature Key Naming

```
✅ Good:
- models.openai
- integrations.bundles.mongodb
- ui.flow_builder.export_flow
- api.batch_execution

❌ Bad:
- openai_models
- MODELS.OPENAI
- ui-export
```

### Default Values

```python
# Basic/Free features - Enable by default
{"enabled": True}

# Premium features - Disable by default
{"enabled": False}
"is_premium": True

# Limit features - Include value
{"enabled": True, "value": 10}
```

### Feature Dependencies

```python
# If feature B requires feature A:
{
    "feature_key": "feature_b",
    "depends_on": ["feature_a"],
}
```

### Frontend Gating

```typescript
// ✅ Good - Single check point
const { isFeatureEnabled } = useFeatureFlags();
if (!isFeatureEnabled("my.feature")) return null;

// ❌ Bad - Scattered checks
if (tier === "pro" || tier === "enterprise") {
  // show feature
}
```

### Performance

1. **Use caching**: Features are cached for 5 minutes
2. **Batch checks**: Get all features at once, not one by one
3. **Frontend filtering**: Filter on frontend when possible
4. **Lazy loading**: Don't load feature-gated components until needed

### Security

1. **Always enforce on backend**: Frontend checks are for UX only
2. **Use middleware**: Centralized enforcement at route level
3. **Audit logging**: Log all feature changes
4. **Superadmin bypass**: Platform superadmins bypass all checks

---

## Troubleshooting

### Feature Not Working

1. **Check user tier assignment**:
   ```sql
   SELECT license_tier_id FROM user WHERE id = 'user-uuid';
   ```

2. **Check tier features**:
   ```sql
   SELECT * FROM license_tier_features 
   WHERE license_tier_id = 'tier-uuid' 
   AND feature_key = 'my.feature';
   ```

3. **Check feature registry**:
   ```sql
   SELECT * FROM feature_registry WHERE feature_key = 'my.feature';
   ```

4. **Clear cache**: Restart backend or wait 5 minutes

### Feature Shows But Shouldn't

1. **Check superadmin status**: Superadmins bypass all checks
2. **Check frontend maps**: Verify feature key in frontend maps
3. **Check middleware**: Ensure route is protected

### API Returns 403

1. **Verify feature is enabled**: Check tier configuration
2. **Check route mapping**: Ensure route pattern matches
3. **Verify user authentication**: User must be logged in

---

## Migration Guide

### Adding a New Feature

1. Add to `seed_features.py`
2. Run backend to seed
3. Configure in tier (Super Admin UI)
4. Add frontend checks if needed

### Removing a Feature

1. Remove from frontend maps
2. Remove frontend checks
3. Keep in registry (mark inactive)
4. Don't delete - for audit trail

### Changing Feature Key

1. Add new feature key
2. Migrate tier configurations
3. Update frontend maps
4. Deprecate old key
5. Remove after migration period

---

## API Reference

### Check Feature (User)

```bash
curl -X GET "https://api.kluisz.com/api/v2/features/check/models.openai" \
  -H "Authorization: Bearer <token>"

# Response
{
  "feature_key": "models.openai",
  "enabled": true,
  "source": "tier"
}
```

### Get All Features (User)

```bash
curl -X GET "https://api.kluisz.com/api/v2/features" \
  -H "Authorization: Bearer <token>"

# Response
{
  "features": {
    "models.openai": {"enabled": true, "source": "tier"},
    "api.webhooks": {"enabled": false, "source": "default"}
  },
  "tier_id": "uuid",
  "tier_name": "Basic",
  "computed_at": "2024-01-01T00:00:00Z"
}
```

### Update Tier Features (Admin)

```bash
curl -X PUT "https://api.kluisz.com/api/v2/features/admin/tiers/{tier_id}" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "models.openai": true,
      "api.webhooks": false,
      "limits.max_flows": {"enabled": true, "value": 50}
    }
  }'
```

---

## Next Steps

- [Adding Custom Bundles](./adding-custom-bundles.md)
- [Contributing Components](./contributing-components.md)
- [Super Admin Guide](../dev/tenant-features/SUPER_ADMIN_UI.md)

---

*Last updated: 2024*


