# Frontend Feature Gating Implementation

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Feature Context Provider                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 useFeatureFlags() Hook                   │   │
│  │                                                         │   │
│  │  • isFeatureEnabled(key: string): boolean               │   │
│  │  • getFeatureValue(key: string): any                    │   │
│  │  • enabledModels: Model[]                               │   │
│  │  • enabledComponents: string[]                          │   │
│  │  • tierName: string                                     │   │
│  │  • isLoading: boolean                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              <FeatureGate> Component                     │   │
│  │                                                         │   │
│  │  <FeatureGate feature="models.openai">                  │   │
│  │    <OpenAISelector />                                   │   │
│  │  </FeatureGate>                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Component-Level Feature Checks                 │   │
│  │                                                         │   │
│  │  const { isFeatureEnabled } = useFeatureFlags();        │   │
│  │  if (isFeatureEnabled("ui.export_flow")) { ... }        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Core Implementation

### 2.1 Feature Context Provider

**Location:** `src/frontend/src/contexts/featureContext.tsx`

```typescript
import { createContext, useContext, useEffect, useMemo, ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/controllers/API/api";

// Types
export interface FeatureValue {
  enabled: boolean;
  value?: any;
  source: "default" | "tier" | "tenant_override";
  expires_at?: string | null;
}

export interface EnabledModel {
  provider: string;
  model_id: string;
  model_name: string;
  model_type: string;
  supports_tools: boolean;
  supports_vision: boolean;
  max_tokens?: number;
}

export interface FeatureContextType {
  // Core methods
  isFeatureEnabled: (featureKey: string) => boolean;
  getFeatureValue: <T = any>(featureKey: string) => T | null;
  
  // Pre-computed lists
  enabledModels: EnabledModel[];
  enabledModelProviders: string[];
  enabledComponents: string[];
  
  // Metadata
  tierName: string | null;
  features: Record<string, FeatureValue>;
  
  // State
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

// Default context
const defaultContext: FeatureContextType = {
  isFeatureEnabled: () => false,
  getFeatureValue: () => null,
  enabledModels: [],
  enabledModelProviders: [],
  enabledComponents: [],
  tierName: null,
  features: {},
  isLoading: true,
  error: null,
  refetch: () => {},
};

const FeatureContext = createContext<FeatureContextType>(defaultContext);

// API calls
async function fetchFeatures() {
  const response = await api.get("/api/v2/features");
  return response.data;
}

async function fetchEnabledModels(): Promise<EnabledModel[]> {
  const response = await api.get("/api/v2/features/models");
  return response.data;
}

async function fetchEnabledComponents(): Promise<string[]> {
  const response = await api.get("/api/v2/features/components");
  return response.data;
}

// Provider component
export function FeatureProvider({ children }: { children: ReactNode }) {
  // Fetch features
  const {
    data: featuresData,
    isLoading: featuresLoading,
    error: featuresError,
    refetch: refetchFeatures,
  } = useQuery({
    queryKey: ["features"],
    queryFn: fetchFeatures,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Fetch enabled models
  const {
    data: modelsData,
    isLoading: modelsLoading,
  } = useQuery({
    queryKey: ["features", "models"],
    queryFn: fetchEnabledModels,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Fetch enabled components
  const {
    data: componentsData,
    isLoading: componentsLoading,
  } = useQuery({
    queryKey: ["features", "components"],
    queryFn: fetchEnabledComponents,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Memoized context value
  const contextValue = useMemo<FeatureContextType>(() => {
    const features = featuresData?.features || {};
    const enabledModels = modelsData || [];
    const enabledComponents = componentsData || [];

    // Extract unique model providers
    const enabledModelProviders = [...new Set(
      enabledModels.map(m => m.provider)
    )];

    return {
      isFeatureEnabled: (featureKey: string): boolean => {
        const feature = features[featureKey];
        if (!feature) return false;
        
        // Check expiration
        if (feature.expires_at) {
          const expires = new Date(feature.expires_at);
          if (expires < new Date()) return false;
        }
        
        return feature.enabled;
      },

      getFeatureValue: <T = any>(featureKey: string): T | null => {
        const feature = features[featureKey];
        if (!feature) return null;
        return feature.value as T;
      },

      enabledModels,
      enabledModelProviders,
      enabledComponents,
      tierName: featuresData?.tier_name || null,
      features,
      isLoading: featuresLoading || modelsLoading || componentsLoading,
      error: featuresError as Error | null,
      refetch: refetchFeatures,
    };
  }, [
    featuresData,
    modelsData,
    componentsData,
    featuresLoading,
    modelsLoading,
    componentsLoading,
    featuresError,
    refetchFeatures,
  ]);

  return (
    <FeatureContext.Provider value={contextValue}>
      {children}
    </FeatureContext.Provider>
  );
}

// Hook
export function useFeatureFlags() {
  const context = useContext(FeatureContext);
  if (!context) {
    throw new Error("useFeatureFlags must be used within a FeatureProvider");
  }
  return context;
}

export default FeatureContext;
```

### 2.2 Feature Gate Component

**Location:** `src/frontend/src/components/common/FeatureGate.tsx`

```typescript
import { ReactNode } from "react";
import { useFeatureFlags } from "@/contexts/featureContext";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Lock } from "lucide-react";

interface FeatureGateProps {
  // Feature to check
  feature: string;
  
  // Children to render if enabled
  children: ReactNode;
  
  // Optional: what to render if disabled
  fallback?: ReactNode;
  
  // Optional: show locked indicator instead of hiding
  showLocked?: boolean;
  lockedMessage?: string;
  
  // Optional: require multiple features (AND logic)
  requireAll?: string[];
  
  // Optional: require any of features (OR logic)
  requireAny?: string[];
}

export function FeatureGate({
  feature,
  children,
  fallback = null,
  showLocked = false,
  lockedMessage = "This feature is not available in your plan",
  requireAll,
  requireAny,
}: FeatureGateProps) {
  const { isFeatureEnabled, tierName } = useFeatureFlags();

  // Check main feature
  let enabled = isFeatureEnabled(feature);

  // Check requireAll (AND logic)
  if (enabled && requireAll?.length) {
    enabled = requireAll.every(f => isFeatureEnabled(f));
  }

  // Check requireAny (OR logic)
  if (!enabled && requireAny?.length) {
    enabled = requireAny.some(f => isFeatureEnabled(f));
  }

  if (enabled) {
    return <>{children}</>;
  }

  if (showLocked) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="relative inline-block opacity-50 cursor-not-allowed">
            {children}
            <div className="absolute inset-0 flex items-center justify-center bg-background/50 rounded">
              <Lock className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{lockedMessage}</p>
          {tierName && <p className="text-xs text-muted-foreground">Current plan: {tierName}</p>}
        </TooltipContent>
      </Tooltip>
    );
  }

  return <>{fallback}</>;
}

// Convenience wrapper for model features
export function ModelGate({
  provider,
  children,
  fallback,
  showLocked,
}: {
  provider: string;
  children: ReactNode;
  fallback?: ReactNode;
  showLocked?: boolean;
}) {
  const featureKey = `models.${provider.toLowerCase()}`;
  return (
    <FeatureGate
      feature={featureKey}
      fallback={fallback}
      showLocked={showLocked}
      lockedMessage={`${provider} models are not available in your plan`}
    >
      {children}
    </FeatureGate>
  );
}

// Convenience wrapper for integration features
export function IntegrationGate({
  integration,
  children,
  fallback,
  showLocked,
}: {
  integration: string;
  children: ReactNode;
  fallback?: ReactNode;
  showLocked?: boolean;
}) {
  const featureKey = `integrations.${integration.toLowerCase()}`;
  return (
    <FeatureGate
      feature={featureKey}
      fallback={fallback}
      showLocked={showLocked}
      lockedMessage={`${integration} integration is not available in your plan`}
    >
      {children}
    </FeatureGate>
  );
}

// Convenience wrapper for UI features
export function UIFeatureGate({
  uiFeature,
  children,
  fallback,
  showLocked,
}: {
  uiFeature: string;
  children: ReactNode;
  fallback?: ReactNode;
  showLocked?: boolean;
}) {
  return (
    <FeatureGate
      feature={`ui.${uiFeature}`}
      fallback={fallback}
      showLocked={showLocked}
    >
      {children}
    </FeatureGate>
  );
}

export default FeatureGate;
```

### 2.3 API Hooks

**Location:** `src/frontend/src/controllers/API/queries/features/index.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/controllers/API/api";

// Types
export interface Feature {
  feature_key: string;
  feature_name: string;
  description: string;
  category: string;
  subcategory?: string;
  feature_type: string;
  default_value: any;
  is_premium: boolean;
  is_active: boolean;
}

export interface TierFeatures {
  tier_id: string;
  features: Record<string, any>;
}

export interface TenantFeatures {
  features: Record<string, any>;
  tier_id?: string;
  tier_name?: string;
  computed_at: string;
}

export interface UpgradeRequest {
  tenant_id: string;
  tenant_name: string;
  feature_key: string;
  requested_at: string;
  notes?: string;
}

// =========================================================================
// FEATURE REGISTRY (Super Admin)
// =========================================================================

export function useFeatureRegistry(category?: string) {
  return useQuery({
    queryKey: ["admin", "features", "registry", category],
    queryFn: async () => {
      const params = category ? `?category=${category}` : "";
      const response = await api.get(`/api/v2/admin/features/registry${params}`);
      return response.data.features as Feature[];
    },
  });
}

// =========================================================================
// TIER FEATURES (Super Admin)
// =========================================================================

export function useTierFeatures(tierId: string) {
  return useQuery({
    queryKey: ["admin", "features", "tier", tierId],
    queryFn: async () => {
      const response = await api.get(`/api/v2/admin/features/tiers/${tierId}`);
      return response.data as TierFeatures;
    },
    enabled: !!tierId,
  });
}

export function useSetTierFeatures() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      tierId,
      features,
    }: {
      tierId: string;
      features: Record<string, any>;
    }) => {
      const response = await api.put(`/api/v2/admin/features/tiers/${tierId}`, {
        features,
      });
      return response.data;
    },
    onSuccess: (_, { tierId }) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "features", "tier", tierId] });
      // Invalidate all tenant features as they inherit from tier
      queryClient.invalidateQueries({ queryKey: ["features"] });
    },
  });
}

// =========================================================================
// TENANT FEATURES (Admin)
// =========================================================================

export function useTenantFeatures(tenantId: string) {
  return useQuery({
    queryKey: ["admin", "features", "tenant", tenantId],
    queryFn: async () => {
      const response = await api.get(`/api/v2/admin/features/tenants/${tenantId}`);
      return response.data as TenantFeatures;
    },
    enabled: !!tenantId,
  });
}

export function useSetTenantOverride() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      tenantId,
      featureKey,
      value,
      validUntil,
      reason,
    }: {
      tenantId: string;
      featureKey: string;
      value: boolean | Record<string, any>;
      validUntil?: string;
      reason?: string;
    }) => {
      const response = await api.post(
        `/api/v2/admin/features/tenants/${tenantId}/override`,
        {
          feature_key: featureKey,
          value,
          valid_until: validUntil,
          reason,
        }
      );
      return response.data;
    },
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "features", "tenant", tenantId] });
      queryClient.invalidateQueries({ queryKey: ["features"] });
    },
  });
}

export function useRemoveTenantOverride() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      tenantId,
      featureKey,
    }: {
      tenantId: string;
      featureKey: string;
    }) => {
      const response = await api.delete(
        `/api/v2/admin/features/tenants/${tenantId}/override/${featureKey}`
      );
      return response.data;
    },
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "features", "tenant", tenantId] });
      queryClient.invalidateQueries({ queryKey: ["features"] });
    },
  });
}

// =========================================================================
// UPGRADE REQUESTS (Super Admin)
// =========================================================================

export function useUpgradeRequests() {
  return useQuery({
    queryKey: ["admin", "features", "upgrade-requests"],
    queryFn: async () => {
      const response = await api.get("/api/v2/admin/features/upgrade-requests");
      return response.data.requests as UpgradeRequest[];
    },
  });
}

export function useApproveUpgrade() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      tenantId,
      featureKey,
      validUntil,
      notes,
    }: {
      tenantId: string;
      featureKey: string;
      validUntil?: string;
      notes?: string;
    }) => {
      const response = await api.post(
        `/api/v2/admin/features/tenants/${tenantId}/upgrade/${featureKey}/approve`,
        { valid_until: validUntil, notes }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "features", "upgrade-requests"] });
      queryClient.invalidateQueries({ queryKey: ["features"] });
    },
  });
}

export function useRejectUpgrade() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      tenantId,
      featureKey,
      reason,
    }: {
      tenantId: string;
      featureKey: string;
      reason?: string;
    }) => {
      const response = await api.post(
        `/api/v2/admin/features/tenants/${tenantId}/upgrade/${featureKey}/reject`,
        { reason }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "features", "upgrade-requests"] });
    },
  });
}
```

## 3. Usage Examples

### 3.1 Model Selector with Feature Gating

```typescript
// src/frontend/src/components/ModelSelector/index.tsx

import { useFeatureFlags } from "@/contexts/featureContext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

export function ModelSelector({ value, onChange }: ModelSelectorProps) {
  const { enabledModels, enabledModelProviders, isLoading } = useFeatureFlags();

  if (isLoading) {
    return <div>Loading models...</div>;
  }

  // Group models by provider
  const modelsByProvider = enabledModels.reduce((acc, model) => {
    if (!acc[model.provider]) acc[model.provider] = [];
    acc[model.provider].push(model);
    return acc;
  }, {} as Record<string, typeof enabledModels>);

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger>
        <SelectValue placeholder="Select a model" />
      </SelectTrigger>
      <SelectContent>
        {Object.entries(modelsByProvider).map(([provider, models]) => (
          <div key={provider}>
            <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground">
              {provider}
            </div>
            {models.map(model => (
              <SelectItem key={model.model_id} value={model.model_id}>
                <div className="flex items-center gap-2">
                  <span>{model.model_name}</span>
                  {model.supports_vision && (
                    <Badge variant="secondary" className="text-xs">Vision</Badge>
                  )}
                  {model.supports_tools && (
                    <Badge variant="secondary" className="text-xs">Tools</Badge>
                  )}
                </div>
              </SelectItem>
            ))}
          </div>
        ))}
      </SelectContent>
    </Select>
  );
}
```

### 3.2 Export Flow Button with Feature Gate

```typescript
// src/frontend/src/components/FlowActions/ExportButton.tsx

import { FeatureGate } from "@/components/common/FeatureGate";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

export function FlowActions({ flowId }: { flowId: string }) {
  return (
    <div className="flex gap-2">
      {/* Always visible */}
      <Button variant="outline" onClick={() => duplicateFlow(flowId)}>
        Duplicate
      </Button>

      {/* Only visible if feature enabled */}
      <FeatureGate feature="ui.flow_builder.export_flow">
        <Button variant="outline" onClick={() => exportFlow(flowId)}>
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </FeatureGate>

      {/* Shows locked indicator if disabled */}
      <FeatureGate 
        feature="ui.flow_builder.share_flow" 
        showLocked
        lockedMessage="Upgrade to share flows with your team"
      >
        <Button variant="outline" onClick={() => shareFlow(flowId)}>
          Share
        </Button>
      </FeatureGate>
    </div>
  );
}
```

### 3.3 MCP Server Section with Integration Gate

```typescript
// src/frontend/src/pages/SettingsPage/MCPServersSection.tsx

import { IntegrationGate } from "@/components/common/FeatureGate";
import { MCPServerList } from "./MCPServerList";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Lock } from "lucide-react";

export function MCPServersSection() {
  return (
    <IntegrationGate
      integration="mcp"
      fallback={
        <Alert>
          <Lock className="h-4 w-4" />
          <AlertDescription>
            MCP Server integration is not available in your current plan.
            Contact your administrator to enable this feature.
          </AlertDescription>
        </Alert>
      }
    >
      <MCPServerList />
    </IntegrationGate>
  );
}
```

### 3.4 Component Palette Filtering

```typescript
// src/frontend/src/components/ComponentPalette/index.tsx

import { useFeatureFlags } from "@/contexts/featureContext";
import { useMemo } from "react";

export function ComponentPalette({ allComponents }: ComponentPaletteProps) {
  const { enabledComponents, isLoading } = useFeatureFlags();

  // Filter components based on enabled features
  const filteredComponents = useMemo(() => {
    if (isLoading) return [];
    
    return allComponents.filter(component => {
      // Always show if no feature restriction
      if (!component.feature_key) return true;
      
      // Check if component's feature is enabled
      return enabledComponents.includes(component.component_key);
    });
  }, [allComponents, enabledComponents, isLoading]);

  return (
    <div className="component-palette">
      {filteredComponents.map(component => (
        <ComponentCard key={component.key} component={component} />
      ))}
    </div>
  );
}
```

### 3.5 Hook for Programmatic Checks

```typescript
// Using the hook directly for programmatic checks

import { useFeatureFlags } from "@/contexts/featureContext";

export function useCanExportFlow() {
  const { isFeatureEnabled } = useFeatureFlags();
  return isFeatureEnabled("ui.flow_builder.export_flow");
}

export function useAvailableModelProviders() {
  const { enabledModelProviders } = useFeatureFlags();
  return enabledModelProviders;
}

// In a component
function SomeComponent() {
  const { isFeatureEnabled, getFeatureValue } = useFeatureFlags();
  
  const handleAction = () => {
    if (!isFeatureEnabled("api.batch_execution")) {
      showUpgradePrompt();
      return;
    }
    
    const maxConcurrent = getFeatureValue<number>("limits.max_concurrent_executions") ?? 1;
    executeBatch(maxConcurrent);
  };
  
  return <Button onClick={handleAction}>Run Batch</Button>;
}
```

## 4. Provider Setup

Add the FeatureProvider to your app's root:

```typescript
// src/frontend/src/App.tsx

import { FeatureProvider } from "@/contexts/featureContext";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <FeatureProvider>
          <RouterProvider router={router} />
        </FeatureProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

## 5. Performance Considerations

1. **Caching**: Features are cached for 5 minutes client-side
2. **Parallel Fetching**: Models and components are fetched in parallel
3. **Memoization**: Context value is memoized to prevent unnecessary re-renders
4. **Lazy Loading**: Features are only fetched after authentication

## 6. Testing

```typescript
// Mock the hook for testing
jest.mock("@/contexts/featureContext", () => ({
  useFeatureFlags: () => ({
    isFeatureEnabled: (key: string) => key === "models.openai",
    enabledModels: [{ provider: "openai", model_id: "gpt-4", model_name: "GPT-4" }],
    enabledComponents: ["ChatOpenAIComponent"],
    tierName: "Professional",
    isLoading: false,
  }),
}));
```




