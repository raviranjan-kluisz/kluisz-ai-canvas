import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/controllers/API/api";

// Types
export interface Feature {
  feature_key: string;
  feature_name: string;
  description: string | null;
  category: string;
  subcategory?: string;
  feature_type: string;
  default_value: Record<string, unknown>;
  is_premium: boolean;
  is_active: boolean;
}

export interface TierFeatures {
  tier_id: string;
  features: Record<string, unknown>;
}

export interface UserFeatures {
  features: Record<string, unknown>;
  tier_id?: string;
  tier_name?: string;
  computed_at: string;
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

// =========================================================================
// USER FEATURES
// =========================================================================

export function useUserFeatures() {
  return useQuery({
    queryKey: ["features"],
    queryFn: async () => {
      const response = await api.get("/api/v2/features");
      return response.data as UserFeatures;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useEnabledModels() {
  return useQuery({
    queryKey: ["features", "models"],
    queryFn: async () => {
      const response = await api.get("/api/v2/features/models");
      return response.data as EnabledModel[];
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useEnabledComponents() {
  return useQuery({
    queryKey: ["features", "components"],
    queryFn: async () => {
      const response = await api.get("/api/v2/features/components");
      return response.data as string[];
    },
    staleTime: 5 * 60 * 1000,
  });
}

// =========================================================================
// USER LIMITS
// =========================================================================

export interface LimitInfo {
  current: number;
  max: number | null;
  unlimited: boolean;
  remaining: number | null;
  percent_used: number;
  period_start?: string;
}

export interface UserLimits {
  user_id: string;
  is_superadmin: boolean;
  message?: string;
  flows?: LimitInfo;
  api_calls?: LimitInfo;
  tier?: {
    id: string;
    name: string;
  };
}

export function useUserLimits() {
  return useQuery({
    queryKey: ["features", "limits"],
    queryFn: async () => {
      const response = await api.get("/api/v2/features/limits");
      return response.data as UserLimits;
    },
    staleTime: 60 * 1000, // 1 minute - more frequent updates for limits
  });
}

// =========================================================================
// FEATURE REGISTRY (Super Admin)
// =========================================================================

export function useFeatureRegistry(category?: string) {
  return useQuery({
    queryKey: ["admin", "features", "registry", category],
    queryFn: async () => {
      const params = category ? `?category=${category}` : "";
      const response = await api.get(`/api/v2/features/admin/registry${params}`);
      return response.data as Feature[];
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
      const response = await api.get(`/api/v2/features/admin/tiers/${tierId}`);
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
      features: Record<string, unknown>;
    }) => {
      const response = await api.put(`/api/v2/features/admin/tiers/${tierId}`, {
        features,
      });
      return response.data;
    },
    onSuccess: (_, { tierId }) => {
      queryClient.invalidateQueries({
        queryKey: ["admin", "features", "tier", tierId],
      });
      // Invalidate all user features as they inherit from tier
      queryClient.invalidateQueries({ queryKey: ["features"] });
    },
  });
}

// =========================================================================
// FEATURE CATEGORIES
// =========================================================================

/**
 * Feature categories for the TierFeatureBuilder UI.
 * 
 * Note: "limits" category is NOT shown in TierFeatureBuilder as limits
 * are configured during license tier creation. Only feature toggles
 * and configurations are shown here.
 * 
 * Categories are organized for optimal admin experience:
 * 1. Models - Most commonly configured (LLM access)
 * 2. Components - Flow builder customization
 * 3. Integrations - Third-party services (bundles, observability)
 * 4. UI Features - Interface customization
 * 5. API - API access control
 */
export const FEATURE_CATEGORIES = {
  models: { 
    title: "Models", 
    icon: "🤖", 
    description: "LLM Provider Access",
    helpText: "Control which AI model providers are available to users",
  },
  components: {
    title: "Components",
    icon: "🧩",
    description: "Flow Builder Blocks",
    helpText: "Configure which component types users can use in flows",
  },
  integrations: {
    title: "Integrations",
    icon: "🔌",
    description: "Third-party Services & Bundles",
    helpText: "Enable/disable external service integrations and component bundles",
  },
  ui: { 
    title: "UI Features", 
    icon: "🎨", 
    description: "User Interface",
    helpText: "Control UI features like chat, embed, code view, etc.",
  },
  api: { 
    title: "API Access", 
    icon: "⚡", 
    description: "API Capabilities",
    helpText: "Configure API access, webhooks, and public endpoints",
  },
  // Note: limits category is intentionally excluded from TierFeatureBuilder
  // Limits are configured during license tier creation (max_flows, max_api_calls, etc.)
} as const;

/**
 * Categories to display in TierFeatureBuilder.
 * This explicitly excludes "limits" which is handled separately.
 */
export const TIER_BUILDER_CATEGORIES = [
  "models",
  "components", 
  "integrations",
  "ui",
  "api",
] as const;

