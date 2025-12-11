/**
 * useFilteredComponents - Hook to filter flow components based on feature flags.
 * 
 * This hook automatically filters component lists based on:
 * 1. Category-level features (e.g., "components.models_and_agents")
 * 2. Component-type features (e.g., "models.openai" for ChatOpenAI)
 * 3. Component metadata (feature_key, required_features)
 * 
 * Use this in the flow sidebar to ensure feature compliance without
 * wrapping each component in FeatureGate.
 * 
 * @example
 * ```tsx
 * const filteredData = useFilteredComponentsByCategory(data);
 * // filteredData only contains components the user has access to
 * ```
 * 
 * @see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md - Pattern 1
 */

import { useMemo } from "react";
import { useFeatureFlags } from "@/contexts/featureContext";
import {
  COMPONENT_CATEGORY_FEATURES,
  COMPONENT_TYPE_FEATURES,
} from "@/constants/feature-maps";
import type { APIClassType } from "@/types/api";

/**
 * Extended component type with optional feature metadata
 */
export interface FeatureAwareComponent extends APIClassType {
  feature_key?: string;
  required_features?: string[];
  any_features?: string[];
}

/**
 * Filter a single category of components based on features.
 * 
 * @param components - Record of component name -> component definition
 * @returns Filtered record with only enabled components
 */
export function useFilteredComponents(
  components: Record<string, FeatureAwareComponent>
): Record<string, FeatureAwareComponent> {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    if (!components || typeof components !== "object") return {};

    const filtered: Record<string, FeatureAwareComponent> = {};

    for (const [key, component] of Object.entries(components)) {
      // Check component-specific feature key (from metadata)
      if (component.feature_key && !isFeatureEnabled(component.feature_key)) {
        continue;
      }

      // Check component type feature (from COMPONENT_TYPE_FEATURES map)
      const typeFeature = COMPONENT_TYPE_FEATURES[key] || 
                          COMPONENT_TYPE_FEATURES[component.display_name || ""];
      if (typeFeature && !isFeatureEnabled(typeFeature)) {
        continue;
      }

      // Check required features (AND logic - all must be enabled)
      if (component.required_features?.length) {
        const allRequired = component.required_features.every((f) =>
          isFeatureEnabled(f)
        );
        if (!allRequired) continue;
      }

      // Check any features (OR logic - at least one must be enabled)
      if (component.any_features?.length) {
        const anyEnabled = component.any_features.some((f) =>
          isFeatureEnabled(f)
        );
        if (!anyEnabled) continue;
      }

      filtered[key] = component;
    }

    return filtered;
  }, [components, isFeatureEnabled]);
}

/**
 * Filter all component categories and their components.
 * 
 * This is the main hook to use in the flow sidebar.
 * It filters both at the category level and component level.
 * 
 * @param data - Record of category name -> components
 * @returns Filtered data with only enabled categories and components
 */
export function useFilteredComponentsByCategory(
  data: Record<string, Record<string, FeatureAwareComponent>>
): Record<string, Record<string, FeatureAwareComponent>> {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    if (!data || typeof data !== "object") return {};

    const filtered: Record<string, Record<string, FeatureAwareComponent>> = {};

    for (const [category, components] of Object.entries(data)) {
      // Check category-level feature
      const categoryFeature = COMPONENT_CATEGORY_FEATURES[category];
      if (categoryFeature && !isFeatureEnabled(categoryFeature)) {
        continue; // Skip entire category
      }

      // Filter individual components within the category
      const filteredComponents: Record<string, FeatureAwareComponent> = {};

      for (const [key, component] of Object.entries(components)) {
        // Check component-specific feature key
        if (component.feature_key && !isFeatureEnabled(component.feature_key)) {
          continue;
        }

        // Check component type feature
        const typeFeature = COMPONENT_TYPE_FEATURES[key] ||
                            COMPONENT_TYPE_FEATURES[component.display_name || ""];
        if (typeFeature && !isFeatureEnabled(typeFeature)) {
          continue;
        }

        // Check required features
        if (component.required_features?.length) {
          const allRequired = component.required_features.every((f) =>
            isFeatureEnabled(f)
          );
          if (!allRequired) continue;
        }

        // Check any features
        if (component.any_features?.length) {
          const anyEnabled = component.any_features.some((f) =>
            isFeatureEnabled(f)
          );
          if (!anyEnabled) continue;
        }

        filteredComponents[key] = component;
      }

      // Only include category if it has components
      if (Object.keys(filteredComponents).length > 0) {
        filtered[category] = filteredComponents;
      }
    }

    return filtered;
  }, [data, isFeatureEnabled]);
}

/**
 * Check if a specific component category is enabled.
 * 
 * @param category - Category name to check
 * @returns true if the category is enabled
 */
export function useIsCategoryEnabled(category: string): boolean {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    const featureKey = COMPONENT_CATEGORY_FEATURES[category];
    
    if (!featureKey) return true; // Unknown category = allow
    
    return isFeatureEnabled(featureKey);
  }, [category, isFeatureEnabled]);
}

/**
 * Check if a specific component type is enabled.
 * 
 * @param componentType - Component type name to check
 * @returns true if the component type is enabled
 */
export function useIsComponentTypeEnabled(componentType: string): boolean {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    const featureKey = COMPONENT_TYPE_FEATURES[componentType];
    
    if (!featureKey) return true; // Unknown type = allow
    
    return isFeatureEnabled(featureKey);
  }, [componentType, isFeatureEnabled]);
}

/**
 * Get list of enabled component categories.
 * 
 * @returns Array of enabled category names
 */
export function useEnabledCategories(): string[] {
  const { isFeatureEnabled } = useFeatureFlags();

  return useMemo(() => {
    const allCategories = Object.keys(COMPONENT_CATEGORY_FEATURES);
    
    return allCategories.filter((category) => {
      const featureKey = COMPONENT_CATEGORY_FEATURES[category];
      return !featureKey || isFeatureEnabled(featureKey);
    });
  }, [isFeatureEnabled]);
}

export default useFilteredComponents;


