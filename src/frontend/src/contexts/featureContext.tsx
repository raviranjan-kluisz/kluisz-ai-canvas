import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useMemo,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/controllers/API/api";
import useAuthStore from "@/stores/authStore";

// Types
export interface FeatureValue {
  enabled: boolean;
  value?: unknown;
  source: "default" | "tier";
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
  getFeatureValue: <T = unknown>(featureKey: string) => T | null;

  // Pre-computed lists
  enabledModels: EnabledModel[];
  enabledModelProviders: string[];
  enabledComponents: string[];

  // Metadata
  tierName: string | null;
  tierId: string | null;
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
  tierId: null,
  features: {},
  isLoading: true,
  error: null,
  refetch: () => {},
};

const FeatureContext = createContext<FeatureContextType>(defaultContext);

// API calls
async function fetchFeatures() {
  try {
    const response = await api.get("/api/v2/features");
    return response.data;
  } catch (error) {
    // Return empty features if API fails (e.g., user not authenticated, server error)
    console.warn("Failed to fetch features:", error);
    return { features: {}, tier_name: null, tier_id: null };
  }
}

async function fetchEnabledModels(): Promise<EnabledModel[]> {
  try {
    const response = await api.get("/api/v2/features/models");
    return response.data;
  } catch (error) {
    console.warn("Failed to fetch enabled models:", error);
    return [];
  }
}

async function fetchEnabledComponents(): Promise<string[]> {
  try {
    const response = await api.get("/api/v2/features/components");
    return response.data;
  } catch (error) {
    console.warn("Failed to fetch enabled components:", error);
    return [];
  }
}

// Provider component
export function FeatureProvider({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

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
    enabled: isAuthenticated,
    retry: false, // Don't retry on error to avoid spamming
  });

  // Fetch enabled models
  const { data: modelsData, isLoading: modelsLoading } = useQuery({
    queryKey: ["features", "models"],
    queryFn: fetchEnabledModels,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: isAuthenticated,
    retry: false,
  });

  // Fetch enabled components
  const { data: componentsData, isLoading: componentsLoading } = useQuery({
    queryKey: ["features", "components"],
    queryFn: fetchEnabledComponents,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: isAuthenticated,
    retry: false,
  });

  // Memoized helper functions
  const isFeatureEnabled = useCallback(
    (featureKey: string): boolean => {
      const features = featuresData?.features || {};
      const feature = features[featureKey];
      if (!feature) return false;

      // Check expiration
      if (feature.expires_at) {
        const expires = new Date(feature.expires_at);
        if (expires < new Date()) return false;
      }

      return feature.enabled;
    },
    [featuresData?.features]
  );

  const getFeatureValue = useCallback(
    <T = unknown,>(featureKey: string): T | null => {
      const features = featuresData?.features || {};
      const feature = features[featureKey];
      if (!feature) return null;
      return feature.value as T;
    },
    [featuresData?.features]
  );

  // Memoized context value
  const contextValue = useMemo<FeatureContextType>(() => {
    // Safely extract data with fallbacks
    const features = (featuresData?.features || {}) as Record<string, FeatureValue>;
    const enabledModels = (Array.isArray(modelsData) ? modelsData : []) as EnabledModel[];
    const enabledComponents = (Array.isArray(componentsData) ? componentsData : []) as string[];

    // Extract unique model providers safely
    const enabledModelProviders = enabledModels.length > 0
      ? enabledModels
          .map((m) => m?.provider)
          .filter((p): p is string => Boolean(p))
          .filter((p, index, arr) => arr.indexOf(p) === index) // Get unique values
      : [];

    return {
      isFeatureEnabled,
      getFeatureValue,
      enabledModels,
      enabledModelProviders,
      enabledComponents,
      tierName: featuresData?.tier_name || null,
      tierId: featuresData?.tier_id || null,
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
    isFeatureEnabled,
    getFeatureValue,
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


