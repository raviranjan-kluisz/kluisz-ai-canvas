# Feature Control System - Extensibility Guide

## Executive Summary

This document outlines architectural patterns to make the Tenant Feature Control System **truly extensible and scalable**. The goal is to **minimize code changes** when adding new features, components, or gates.

**Current State**: Feature gates exist but are scattered across individual components, requiring manual code changes for each new feature.

**Target State**: A **metadata-driven** approach where new features self-register and are automatically enforced throughout the application.

---

## Table of Contents

1. [Current Architecture Gaps](#1-current-architecture-gaps)
2. [Design Principles](#2-design-principles)
3. [Pattern 1: Metadata-Driven Component Gating](#3-pattern-1-metadata-driven-component-gating)
4. [Pattern 2: Backend Route Middleware](#4-pattern-2-backend-route-middleware)
5. [Pattern 3: Model Provider Interceptor](#5-pattern-3-model-provider-interceptor)
6. [Pattern 4: UI Element Feature Maps](#6-pattern-4-ui-element-feature-maps)
7. [Pattern 5: Event-Driven Feature Enforcement](#7-pattern-5-event-driven-feature-enforcement)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Feature Key Conventions](#9-feature-key-conventions)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Current Architecture Gaps

### What Exists (Good)

| Component | Status | Description |
|-----------|--------|-------------|
| Database Schema | ✅ Complete | `feature_registry`, `license_tier_features`, registries |
| FeatureControlService | ✅ Complete | Caching, resolution, audit logging |
| `useFeatureFlags` Hook | ✅ Complete | React context with feature resolution |
| `FeatureGate` Component | ✅ Complete | Declarative gating wrapper |
| `require_feature` Decorator | ✅ Complete | Backend endpoint protection |

### What's Missing (Gaps)

| Gap | Impact | Current Workaround |
|-----|--------|-------------------|
| **Manual component gating** | Each UI element needs `<FeatureGate>` wrapper | None - features leak through |
| **No automatic model filtering** | All models shown regardless of tier | Manual dropdown filtering |
| **Route-by-route protection** | Each endpoint needs decorator | Most endpoints unprotected |
| **No component registry integration** | `component_registry` not used for filtering | Hardcoded component lists |
| **Scattered feature checks** | Gates in ~7 of 200+ files | Incomplete coverage |

### The Problem

```
Current: Add new feature → Modify 5-10 files → Test each location → Deploy
Target:  Add new feature → Add to registry → Automatically enforced everywhere
```

---

## 2. Design Principles

### 2.1 Single Source of Truth

All feature definitions live in `feature_registry`. No feature keys hardcoded in application code.

```sql
-- This is the ONLY place features are defined
INSERT INTO feature_registry (feature_key, feature_name, category, ...)
VALUES ('models.openai', 'OpenAI Models', 'models', ...);
```

### 2.2 Metadata-Driven Enforcement

Components, routes, and UI elements declare their feature requirements via metadata, not code.

```typescript
// BAD: Feature check in component code
if (isFeatureEnabled('models.openai')) {
  showOpenAIOption();
}

// GOOD: Component metadata declares its feature
const componentDef = {
  name: 'OpenAIComponent',
  feature_key: 'models.openai',  // Automatically filtered
};
```

### 2.3 Fail-Closed Security

If a feature check fails or is ambiguous, deny access. Features must be explicitly enabled.

### 2.4 Central Configuration

Feature-to-resource mappings defined in single configuration files, not scattered across codebase.

---

## 3. Pattern 1: Metadata-Driven Component Gating

### Concept

Instead of wrapping each component with `<FeatureGate>`, components declare their feature requirements in their type definitions. A single filtering layer applies all gates automatically.

### Implementation

#### 3.1 Extend Component Type Definition

```typescript
// src/frontend/src/types/api/index.ts

export interface APIClassType {
  name: string;
  display_name: string;
  description: string;
  // ... existing fields ...
  
  // NEW: Feature gating metadata
  feature_key?: string;           // Primary feature required
  required_features?: string[];   // All must be enabled
  any_features?: string[];        // At least one must be enabled
}
```

#### 3.2 Create Component Filter Hook

```typescript
// src/frontend/src/hooks/useFilteredComponents.ts

import { useMemo } from 'react';
import { useFeatureFlags } from '@/contexts/featureContext';
import type { APIClassType } from '@/types/api';

export function useFilteredComponents(
  components: Record<string, APIClassType>
): Record<string, APIClassType> {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    const filtered: Record<string, APIClassType> = {};

    for (const [key, component] of Object.entries(components)) {
      // Check primary feature
      if (component.feature_key && !isFeatureEnabled(component.feature_key)) {
        continue;
      }

      // Check required features (AND logic)
      if (component.required_features?.length) {
        const allRequired = component.required_features.every(f => 
          isFeatureEnabled(f)
        );
        if (!allRequired) continue;
      }

      // Check any features (OR logic)
      if (component.any_features?.length) {
        const anyEnabled = component.any_features.some(f => 
          isFeatureEnabled(f)
        );
        if (!anyEnabled) continue;
      }

      filtered[key] = component;
    }

    return filtered;
  }, [components, isFeatureEnabled]);
}
```

#### 3.3 Apply in Flow Sidebar (Single Location)

```typescript
// src/frontend/src/pages/FlowPage/components/flowSidebarComponent/index.tsx

import { useFilteredComponents } from '@/hooks/useFilteredComponents';

export function FlowSidebarComponent() {
  const rawData = useTypesStore((state) => state.data);
  
  // Single filter that applies ALL feature gates
  const data = useMemo(() => {
    const filtered: typeof rawData = {};
    for (const [category, components] of Object.entries(rawData)) {
      filtered[category] = useFilteredComponents(components);
    }
    return filtered;
  }, [rawData]);

  // ... rest of component uses filtered data
}
```

#### 3.4 Populate Feature Keys from Backend

The backend should send component metadata including feature keys:

```python
# When building component types, include feature requirements
def get_component_types():
    components = load_all_components()
    
    # Enrich with feature keys from component_registry
    for comp in components:
        registry_entry = get_component_registry(comp.name)
        if registry_entry:
            comp.feature_key = registry_entry.feature_key
            comp.required_features = registry_entry.required_features
    
    return components
```

### Benefits

- **Add new component**: Set `feature_key` in registry → automatically filtered
- **Change feature requirement**: Update registry → automatically applied
- **No UI code changes needed** for new components

---

## 4. Pattern 2: Backend Route Middleware

### Concept

Instead of decorating each endpoint with `@require_feature()`, define a central route-to-feature mapping that middleware enforces automatically.

### Implementation

#### 4.1 Route Feature Configuration

```python
# src/backend/base/kluisz/api/middleware/route_features.py

from typing import Dict, List
import re

# Central configuration: route patterns → required features
ROUTE_FEATURE_MAP: Dict[str, List[str]] = {
    # MCP endpoints
    r"/api/v[12]/mcp/.*": ["integrations.mcp", "ui.advanced.mcp_server_config"],
    
    # Custom components
    r"/api/v[12]/custom-components.*": ["components.custom.enabled"],
    r"/api/v[12]/components/.*/code": ["components.custom.code_editing"],
    
    # Flow operations
    r"/api/v[12]/flows/.*/export": ["ui.flow_builder.export_flow"],
    r"/api/v[12]/flows/.*/import": ["ui.flow_builder.import_flow"],
    r"/api/v[12]/flows/.*/share": ["ui.flow_builder.share_flow"],
    r"/api/v[12]/flows/.*/versions": ["ui.flow_builder.version_control"],
    
    # API access
    r"/api/v[12]/api-keys.*": ["ui.advanced.api_keys_management"],
    r"/api/v[12]/webhooks.*": ["api.webhooks"],
    
    # Integrations
    r"/api/v[12]/integrations/langfuse.*": ["integrations.langfuse"],
    r"/api/v[12]/integrations/langsmith.*": ["integrations.langsmith"],
    
    # Vector stores
    r"/api/v[12]/vector-stores/pinecone.*": ["integrations.vector_stores.pinecone"],
    r"/api/v[12]/vector-stores/qdrant.*": ["integrations.vector_stores.qdrant"],
}

# Routes that bypass feature checks (public, auth, health)
EXEMPT_ROUTES = [
    r"/api/v[12]/health",
    r"/api/v[12]/login",
    r"/api/v[12]/register",
    r"/api/v[12]/refresh",
    r"/api/v[12]/features.*",  # Feature API itself
    r"/docs",
    r"/openapi.json",
]


def get_required_features(path: str) -> List[str]:
    """Get required features for a route path."""
    # Check exemptions first
    for pattern in EXEMPT_ROUTES:
        if re.match(pattern, path):
            return []
    
    # Find matching feature requirements
    for pattern, features in ROUTE_FEATURE_MAP.items():
        if re.match(pattern, path):
            return features
    
    return []  # No specific requirements


def is_route_exempt(path: str) -> bool:
    """Check if route is exempt from feature checks."""
    return any(re.match(pattern, path) for pattern in EXEMPT_ROUTES)
```

#### 4.2 Feature Enforcement Middleware

```python
# src/backend/base/kluisz/api/middleware/feature_middleware.py

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from kluisz.api.middleware.route_features import get_required_features, is_route_exempt
from kluisz.services.features.control_service import FeatureControlService
from kluisz.services.auth.utils import get_current_user_from_request


class FeatureEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically enforces feature requirements based on route patterns.
    
    This eliminates the need to decorate each endpoint individually.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Skip exempt routes
        if is_route_exempt(path):
            return await call_next(request)
        
        # Get required features for this route
        required_features = get_required_features(path)
        
        if not required_features:
            # No specific requirements, allow
            return await call_next(request)
        
        # Get current user
        try:
            user = await get_current_user_from_request(request)
        except Exception:
            # Not authenticated - let auth middleware handle it
            return await call_next(request)
        
        if not user:
            return await call_next(request)
        
        # Superadmins bypass all feature checks
        if user.is_platform_superadmin:
            return await call_next(request)
        
        # Check features (OR logic - any enabled feature allows access)
        service = FeatureControlService()
        
        for feature_key in required_features:
            if await service.is_feature_enabled(str(user.id), feature_key):
                return await call_next(request)
        
        # No required features are enabled
        return JSONResponse(
            status_code=403,
            content={
                "detail": f"Feature not available in your plan. Required: {', '.join(required_features)}",
                "required_features": required_features,
                "upgrade_url": "/settings/subscription",
            },
        )
```

#### 4.3 Register Middleware

```python
# src/backend/base/kluisz/main.py

from kluisz.api.middleware.feature_middleware import FeatureEnforcementMiddleware

def create_app():
    app = FastAPI(...)
    
    # Add feature enforcement middleware
    app.add_middleware(FeatureEnforcementMiddleware)
    
    return app
```

### Benefits

- **Add new protected route**: Add one line to `ROUTE_FEATURE_MAP`
- **Change feature requirement**: Update mapping → immediately applied
- **No endpoint code changes needed**
- **Centralized security audit** - all protected routes in one file

---

## 5. Pattern 3: Model Provider Interceptor

### Concept

Create a single hook that filters models by feature flags, used by ALL model selection components.

### Implementation

#### 5.1 Model Filter Hook

```typescript
// src/frontend/src/hooks/useFilteredModels.ts

import { useMemo } from 'react';
import { useFeatureFlags } from '@/contexts/featureContext';

interface Model {
  provider: string;
  model_id: string;
  model_name: string;
  model_type?: string;
  // ... other fields
}

// Provider to feature key mapping
const PROVIDER_FEATURE_MAP: Record<string, string> = {
  openai: 'models.openai',
  anthropic: 'models.anthropic',
  google: 'models.google',
  mistral: 'models.mistral',
  ollama: 'models.ollama',
  azure_openai: 'models.azure_openai',
  aws_bedrock: 'models.aws_bedrock',
  ibm_watsonx: 'models.ibm_watsonx',
  groq: 'models.groq',
  xai: 'models.xai',
};

export function useFilteredModels<T extends Model>(models: T[]): T[] {
  const { isFeatureEnabled, enabledModelProviders } = useFeatureFlags();

  return useMemo(() => {
    return models.filter((model) => {
      const featureKey = PROVIDER_FEATURE_MAP[model.provider.toLowerCase()];
      
      // If no feature key mapping, allow (backwards compatibility)
      if (!featureKey) return true;
      
      return isFeatureEnabled(featureKey);
    });
  }, [models, isFeatureEnabled]);
}

// Convenience hook for provider list
export function useEnabledProviders(): string[] {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    return Object.entries(PROVIDER_FEATURE_MAP)
      .filter(([_, featureKey]) => isFeatureEnabled(featureKey))
      .map(([provider]) => provider);
  }, [isFeatureEnabled]);
}
```

#### 5.2 Usage in Model Selectors

```typescript
// Any component with model selection
import { useFilteredModels } from '@/hooks/useFilteredModels';

function ModelSelector({ allModels }: { allModels: Model[] }) {
  const models = useFilteredModels(allModels);
  
  return (
    <Select>
      {models.map(model => (
        <SelectItem key={model.model_id} value={model.model_id}>
          {model.model_name}
        </SelectItem>
      ))}
    </Select>
  );
}
```

### Benefits

- **Add new model provider**: Add to `PROVIDER_FEATURE_MAP` → automatically filtered
- **All model dropdowns respect features** automatically
- **Single source of truth** for provider-to-feature mapping

---

## 6. Pattern 4: UI Element Feature Maps

### Concept

Define UI element visibility in configuration maps, not scattered `<FeatureGate>` wrappers.

### Implementation

#### 6.1 Feature Map Definitions

```typescript
// src/frontend/src/constants/feature-maps.ts

/**
 * Maps UI elements/routes to their required features.
 * Single source of truth for all UI-level feature gating.
 */

// Sidebar navigation items
export const SETTINGS_SIDEBAR_FEATURES: Record<string, string[]> = {
  'mcp-servers': ['integrations.mcp', 'ui.advanced.mcp_server_config'],
  'api-keys': ['ui.advanced.api_keys_management'],
  'global-variables': ['ui.advanced.global_variables'],
  'store': ['ui.store.enabled'],
};

// Flow toolbar actions
export const FLOW_TOOLBAR_FEATURES: Record<string, string[]> = {
  'export': ['ui.flow_builder.export_flow'],
  'import': ['ui.flow_builder.import_flow'],
  'share': ['ui.flow_builder.share_flow'],
  'duplicate': ['ui.flow_builder.duplicate_flow'],
  'version-history': ['ui.flow_builder.version_control'],
};

// Node toolbar actions
export const NODE_TOOLBAR_FEATURES: Record<string, string[]> = {
  'code': ['components.custom.code_editing', 'ui.code_view.edit_code'],
  'save-component': ['components.custom.enabled'],
  'share': ['ui.flow_builder.share_flow'],
};

// Component categories in sidebar
export const COMPONENT_CATEGORY_FEATURES: Record<string, string> = {
  'models_and_agents': 'components.models_and_agents',
  'helpers': 'components.helpers',
  'data_io': 'components.data_io',
  'logic': 'components.logic',
  'embeddings': 'components.embeddings',
  'memories': 'components.memories',
  'tools': 'components.tools',
  'prototypes': 'components.prototypes',
  'MCP': 'integrations.mcp',
};

// Debug/Advanced features
export const DEBUG_FEATURES: Record<string, string> = {
  'step-execution': 'ui.debug.step_execution',
  'logs-access': 'ui.debug.logs_access',
  'debug-mode': 'ui.debug.enabled',
};
```

#### 6.2 Feature Check Utility

```typescript
// src/frontend/src/utils/feature-utils.ts

import { SETTINGS_SIDEBAR_FEATURES, FLOW_TOOLBAR_FEATURES, ... } from '@/constants/feature-maps';

type FeatureMap = Record<string, string | string[]>;

export function isUIElementEnabled(
  elementKey: string,
  featureMap: FeatureMap,
  isFeatureEnabled: (key: string) => boolean,
): boolean {
  const features = featureMap[elementKey];
  
  if (!features) return true; // Not in map = always visible
  
  const featureList = Array.isArray(features) ? features : [features];
  
  // OR logic: any enabled feature allows access
  return featureList.some(f => isFeatureEnabled(f));
}

// Convenience function to filter a list of items
export function filterByFeatures<T extends { key: string }>(
  items: T[],
  featureMap: FeatureMap,
  isFeatureEnabled: (key: string) => boolean,
): T[] {
  return items.filter(item => 
    isUIElementEnabled(item.key, featureMap, isFeatureEnabled)
  );
}
```

#### 6.3 Usage Example

```typescript
// Settings page sidebar
import { SETTINGS_SIDEBAR_FEATURES } from '@/constants/feature-maps';
import { isUIElementEnabled } from '@/utils/feature-utils';

function SettingsPage() {
  const { isFeatureEnabled } = useFeatureFlags();
  
  const sidebarItems = [
    { key: 'general', title: 'General', href: '/settings/general' },
    { key: 'mcp-servers', title: 'MCP Servers', href: '/settings/mcp-servers' },
    { key: 'api-keys', title: 'API Keys', href: '/settings/api-keys' },
    // ... more items
  ];
  
  const visibleItems = sidebarItems.filter(item =>
    isUIElementEnabled(item.key, SETTINGS_SIDEBAR_FEATURES, isFeatureEnabled)
  );
  
  return <Sidebar items={visibleItems} />;
}
```

### Benefits

- **Add new UI element**: Add to feature map → automatically gated
- **Change feature requirement**: Update map → immediately applied
- **Single file contains all UI visibility rules**
- **Easy to audit** which features gate which UI elements

---

## 7. Pattern 5: Event-Driven Feature Enforcement

### Concept

For complex operations (flow execution, API calls), use an event system that validates features before execution.

### Implementation

#### 7.1 Feature Validation Service

```python
# src/backend/base/kluisz/services/features/validation_service.py

from typing import Dict, List, Any
from dataclasses import dataclass

from kluisz.services.features.control_service import FeatureControlService


@dataclass
class FeatureValidationResult:
    allowed: bool
    missing_features: List[str]
    message: str


class FeatureValidationService:
    """
    Validates feature requirements for complex operations.
    """
    
    # Operation to feature requirements
    OPERATION_FEATURES: Dict[str, List[str]] = {
        'execute_flow': [],  # Basic execution always allowed
        'execute_flow_with_streaming': ['api.streaming_responses'],
        'execute_batch': ['api.batch_execution'],
        'use_model': [],  # Checked separately per model
        'create_webhook': ['api.webhooks'],
        'export_flow': ['ui.flow_builder.export_flow'],
        'import_flow': ['ui.flow_builder.import_flow'],
        'share_flow': ['ui.flow_builder.share_flow'],
        'use_mcp_server': ['integrations.mcp'],
        'create_custom_component': ['components.custom.enabled'],
        'edit_component_code': ['components.custom.code_editing'],
    }
    
    def __init__(self):
        self.feature_service = FeatureControlService()
    
    async def validate_operation(
        self,
        user_id: str,
        operation: str,
        context: Dict[str, Any] = None,
    ) -> FeatureValidationResult:
        """
        Validate if user can perform an operation.
        
        Args:
            user_id: User UUID
            operation: Operation name from OPERATION_FEATURES
            context: Additional context (e.g., model_provider for use_model)
        
        Returns:
            FeatureValidationResult with allowed status and details
        """
        context = context or {}
        
        # Get required features
        required = self.OPERATION_FEATURES.get(operation, [])
        
        # Handle special cases
        if operation == 'use_model' and 'provider' in context:
            provider = context['provider'].lower()
            required = [f'models.{provider}']
        
        if not required:
            return FeatureValidationResult(
                allowed=True,
                missing_features=[],
                message='Operation allowed',
            )
        
        # Check features
        missing = []
        for feature_key in required:
            if not await self.feature_service.is_feature_enabled(user_id, feature_key):
                missing.append(feature_key)
        
        if missing:
            return FeatureValidationResult(
                allowed=False,
                missing_features=missing,
                message=f'Features required: {", ".join(missing)}',
            )
        
        return FeatureValidationResult(
            allowed=True,
            missing_features=[],
            message='Operation allowed',
        )
```

#### 7.2 Integration with Flow Execution

```python
# In flow execution service

async def execute_flow(self, flow_id: str, user_id: str, options: dict):
    # Validate execution features
    validation = await self.validation_service.validate_operation(
        user_id,
        'execute_flow_with_streaming' if options.get('streaming') else 'execute_flow',
    )
    
    if not validation.allowed:
        raise FeatureNotEnabled(validation.missing_features, validation.message)
    
    # Validate model usage
    for node in flow.nodes:
        if node.type == 'model':
            model_validation = await self.validation_service.validate_operation(
                user_id,
                'use_model',
                {'provider': node.data.provider},
            )
            if not model_validation.allowed:
                raise FeatureNotEnabled(
                    model_validation.missing_features,
                    f'Model {node.data.provider} not available in your plan',
                )
    
    # Proceed with execution
    ...
```

### Benefits

- **Complex validation logic** centralized
- **Operation names are self-documenting**
- **Easy to add new operations** with their requirements
- **Context-aware validation** (e.g., different models have different requirements)

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1)

1. **Create feature map constants**
   - `src/frontend/src/constants/feature-maps.ts`
   - Define all UI element → feature mappings

2. **Create filter hooks**
   - `useFilteredComponents`
   - `useFilteredModels`
   - `filterByFeatures` utility

3. **Create route feature configuration**
   - `route_features.py` with all mappings
   - Keep endpoint decorators as backup

### Phase 2: Middleware (Week 2)

4. **Implement backend middleware**
   - `FeatureEnforcementMiddleware`
   - Register in FastAPI app
   - Test all protected routes

5. **Apply component filter in sidebar**
   - Single location filtering
   - Remove individual `<FeatureGate>` wrappers

### Phase 3: Validation (Week 3)

6. **Implement validation service**
   - `FeatureValidationService`
   - Integrate with flow execution
   - Integrate with API operations

7. **Add component metadata**
   - Backend: Include `feature_key` in component types
   - Frontend: Use metadata for filtering

### Phase 4: Cleanup (Week 4)

8. **Audit and remove redundant gates**
   - Remove scattered `<FeatureGate>` wrappers
   - Remove individual `@require_feature` decorators
   - Ensure all protection via maps/middleware

9. **Documentation and testing**
   - Update all documentation
   - Add feature gate tests
   - Create audit report

---

## 9. Feature Key Conventions

### Naming Rules

```
category.subcategory.item.variant
```

| Level | Examples | Description |
|-------|----------|-------------|
| Category | `models`, `components`, `ui`, `api`, `integrations`, `limits` | Top-level grouping |
| Subcategory | `openai`, `custom`, `flow_builder`, `advanced` | Feature area |
| Item | `gpt4`, `enabled`, `export_flow`, `api_keys_management` | Specific feature |
| Variant | `turbo`, `mini` | Optional variant |

### Examples

```
models.openai           # All OpenAI models
models.openai.gpt4      # Specific model
components.custom.enabled
components.custom.code_editing
ui.flow_builder.export_flow
ui.advanced.mcp_server_config
integrations.mcp
integrations.vector_stores.pinecone
api.webhooks
api.streaming_responses
limits.max_flows
```

### Adding New Features

1. Add to `feature_registry` table with proper category/subcategory
2. Add to appropriate feature map (`ROUTE_FEATURE_MAP`, `COMPONENT_CATEGORY_FEATURES`, etc.)
3. Features are automatically enforced - no code changes needed

---

## 10. Testing Strategy

### Unit Tests

```typescript
// Test feature filtering
describe('useFilteredComponents', () => {
  it('filters components by feature key', () => {
    const components = {
      OpenAI: { name: 'OpenAI', feature_key: 'models.openai' },
      Anthropic: { name: 'Anthropic', feature_key: 'models.anthropic' },
    };
    
    // Mock only OpenAI enabled
    mockIsFeatureEnabled.mockImplementation(key => key === 'models.openai');
    
    const result = useFilteredComponents(components);
    
    expect(Object.keys(result)).toEqual(['OpenAI']);
  });
});
```

### Integration Tests

```python
# Test middleware enforcement
async def test_mcp_endpoint_requires_feature():
    # User without MCP feature
    user = create_user_without_feature('integrations.mcp')
    
    response = await client.get(
        '/api/v2/mcp/servers',
        headers={'Authorization': f'Bearer {user.token}'},
    )
    
    assert response.status_code == 403
    assert 'integrations.mcp' in response.json()['required_features']
```

### Audit Report

Generate periodic reports:

```sql
-- Features with no protection
SELECT fr.feature_key, fr.feature_name
FROM feature_registry fr
WHERE fr.feature_key NOT IN (
  SELECT DISTINCT unnest(string_to_array(features, ','))
  FROM route_feature_map
)
AND fr.category NOT IN ('limits');

-- Routes with no feature protection
SELECT route_pattern
FROM all_routes
WHERE route_pattern NOT IN (SELECT pattern FROM route_feature_map)
AND route_pattern NOT LIKE '%/health%'
AND route_pattern NOT LIKE '%/login%';
```

---

## Summary

| Pattern | What It Solves | Files to Modify When Adding Feature |
|---------|---------------|-------------------------------------|
| Metadata-Driven Components | Component visibility | 0 (just registry) |
| Route Middleware | API protection | 1 (`route_features.py`) |
| Model Interceptor | Model filtering | 1 (`PROVIDER_FEATURE_MAP`) |
| UI Feature Maps | UI element visibility | 1 (`feature-maps.ts`) |
| Validation Service | Complex operations | 1 (`OPERATION_FEATURES`) |

**Goal Achieved**: Adding a new feature requires updating **1-2 configuration files**, not **10-20 component files**.

---

## References

- [Architecture Overview](./architecture.md)
- [Backend Service](./backend_service.md)
- [Frontend Gates](./frontend_gates.md)
- [Super Admin UI](./super_admin_ui.md)
