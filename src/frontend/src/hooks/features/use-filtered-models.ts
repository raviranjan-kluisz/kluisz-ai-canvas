/**
 * useFilteredModels - Hook to filter models based on feature flags.
 * 
 * This hook automatically filters model lists based on the user's enabled
 * model provider features. Use this in ANY model dropdown to ensure
 * feature compliance.
 * 
 * @example
 * ```tsx
 * const models = useFilteredModels(allModels);
 * // models only contains providers the user has access to
 * ```
 * 
 * @see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md - Pattern 3
 */

import { useMemo } from "react";
import { useFeatureFlags } from "@/contexts/featureContext";
import { PROVIDER_FEATURE_MAP } from "@/constants/feature-maps";

/**
 * Base model interface - extend as needed
 */
export interface BaseModel {
  provider: string;
  model_id?: string;
  model_name?: string;
  name?: string;
  [key: string]: unknown;
}

/**
 * Filter models based on enabled provider features.
 * 
 * @param models - Array of models to filter
 * @returns Filtered array containing only models from enabled providers
 */
export function useFilteredModels<T extends BaseModel>(models: T[]): T[] {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    if (!models || !Array.isArray(models)) return [];

    return models.filter((model) => {
      const provider = model.provider?.toLowerCase();
      
      if (!provider) return true; // No provider = allow (backwards compat)
      
      const featureKey = PROVIDER_FEATURE_MAP[provider];
      
      // If no feature key mapping exists, allow (unknown provider)
      if (!featureKey) return true;
      
      return isFeatureEnabled(featureKey);
    });
  }, [models, isFeatureEnabled]);
}

/**
 * Get list of enabled model providers.
 * 
 * @returns Array of enabled provider names (lowercase)
 */
export function useEnabledProviders(): string[] {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    return Object.entries(PROVIDER_FEATURE_MAP)
      .filter(([_, featureKey]) => isFeatureEnabled(featureKey))
      .map(([provider]) => provider);
  }, [isFeatureEnabled]);
}

/**
 * Check if a specific provider is enabled.
 * 
 * @param provider - Provider name to check
 * @returns true if the provider is enabled
 */
export function useIsProviderEnabled(provider: string): boolean {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    const normalizedProvider = provider?.toLowerCase();
    const featureKey = PROVIDER_FEATURE_MAP[normalizedProvider];
    
    if (!featureKey) return true; // Unknown provider = allow
    
    return isFeatureEnabled(featureKey);
  }, [provider, isFeatureEnabled]);
}

/**
 * Filter a record/object of models by provider.
 * 
 * @param modelsRecord - Record where keys are model IDs and values are model objects
 * @returns Filtered record with only enabled providers
 */
export function useFilteredModelsRecord<T extends BaseModel>(
  modelsRecord: Record<string, T>
): Record<string, T> {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    if (!modelsRecord || typeof modelsRecord !== "object") return {};

    const filtered: Record<string, T> = {};

    for (const [key, model] of Object.entries(modelsRecord)) {
      const provider = model.provider?.toLowerCase();
      
      if (!provider) {
        filtered[key] = model;
        continue;
      }
      
      const featureKey = PROVIDER_FEATURE_MAP[provider];
      
      if (!featureKey || isFeatureEnabled(featureKey)) {
        filtered[key] = model;
      }
    }

    return filtered;
  }, [modelsRecord, isFeatureEnabled]);
}

export default useFilteredModels;


