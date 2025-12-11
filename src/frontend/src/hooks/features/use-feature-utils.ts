/**
 * useFeatureUtils - Utility hooks and functions for feature checking.
 * 
 * These utilities work with the feature maps to provide consistent
 * feature checking across the application.
 * 
 * @see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md - Pattern 4
 */

import { useMemo, useCallback } from "react";
import { useFeatureFlags } from "@/contexts/featureContext";
import type { FeatureMap } from "@/constants/feature-maps";
import {
  SETTINGS_SIDEBAR_FEATURES,
  FLOW_TOOLBAR_FEATURES,
  NODE_TOOLBAR_FEATURES,
  DEBUG_FEATURES,
  INTEGRATION_FEATURES,
  SIDEBAR_SEGMENT_FEATURES,
  API_OPERATION_FEATURES,
} from "@/constants/feature-maps";

/**
 * Check if a UI element is enabled based on its feature requirements.
 * 
 * @param elementKey - The key of the element in the feature map
 * @param featureMap - The feature map to check against
 * @param isFeatureEnabled - Function to check if a feature is enabled
 * @returns true if the element should be visible
 */
export function isUIElementEnabled(
  elementKey: string,
  featureMap: FeatureMap,
  isFeatureEnabled: (key: string) => boolean
): boolean {
  const features = featureMap[elementKey];

  if (!features) return true; // Not in map = always visible

  const featureList = Array.isArray(features) ? features : [features];

  if (featureList.length === 0) return true; // Empty array = always visible

  // OR logic: any enabled feature allows access
  return featureList.some((f) => isFeatureEnabled(f));
}

/**
 * Filter a list of items based on feature requirements.
 * 
 * @param items - Array of items with a `key` property
 * @param featureMap - The feature map to check against
 * @param isFeatureEnabled - Function to check if a feature is enabled
 * @returns Filtered array with only enabled items
 */
export function filterByFeatures<T extends { key: string }>(
  items: T[],
  featureMap: FeatureMap,
  isFeatureEnabled: (key: string) => boolean
): T[] {
  return items.filter((item) =>
    isUIElementEnabled(item.key, featureMap, isFeatureEnabled)
  );
}

/**
 * Hook to check settings sidebar item visibility.
 */
export function useSettingsSidebarFeatures() {
  const { isFeatureEnabled } = useFeatureFlags();

  const isItemEnabled = useCallback(
    (itemKey: string) =>
      isUIElementEnabled(itemKey, SETTINGS_SIDEBAR_FEATURES, isFeatureEnabled),
    [isFeatureEnabled]
  );

  const filterItems = useCallback(
    <T extends { key: string }>(items: T[]) =>
      filterByFeatures(items, SETTINGS_SIDEBAR_FEATURES, isFeatureEnabled),
    [isFeatureEnabled]
  );

  return { isItemEnabled, filterItems };
}

/**
 * Hook to check flow toolbar action visibility.
 */
export function useFlowToolbarFeatures() {
  const { isFeatureEnabled } = useFeatureFlags();

  const isActionEnabled = useCallback(
    (actionKey: string) =>
      isUIElementEnabled(actionKey, FLOW_TOOLBAR_FEATURES, isFeatureEnabled),
    [isFeatureEnabled]
  );

  const filterActions = useCallback(
    <T extends { key: string }>(actions: T[]) =>
      filterByFeatures(actions, FLOW_TOOLBAR_FEATURES, isFeatureEnabled),
    [isFeatureEnabled]
  );

  return { isActionEnabled, filterActions };
}

/**
 * Hook to check node toolbar action visibility.
 */
export function useNodeToolbarFeatures() {
  const { isFeatureEnabled } = useFeatureFlags();

  const isActionEnabled = useCallback(
    (actionKey: string) =>
      isUIElementEnabled(actionKey, NODE_TOOLBAR_FEATURES, isFeatureEnabled),
    [isFeatureEnabled]
  );

  return { isActionEnabled };
}

/**
 * Hook to check debug feature availability.
 */
export function useDebugFeatures() {
  const { isFeatureEnabled } = useFeatureFlags();

  const isDebugFeatureEnabled = useCallback(
    (featureKey: string) => {
      const fullKey = DEBUG_FEATURES[featureKey];
      if (!fullKey) return true;
      return isFeatureEnabled(fullKey);
    },
    [isFeatureEnabled]
  );

  const enabledDebugFeatures = useMemo(() => {
    return Object.entries(DEBUG_FEATURES)
      .filter(([_, featureKey]) => isFeatureEnabled(featureKey))
      .map(([key]) => key);
  }, [isFeatureEnabled]);

  return { isDebugFeatureEnabled, enabledDebugFeatures };
}

/**
 * Hook to check integration availability.
 */
export function useIntegrationFeatures() {
  const { isFeatureEnabled } = useFeatureFlags();

  const isIntegrationEnabled = useCallback(
    (integrationKey: string) => {
      const featureKey = INTEGRATION_FEATURES[integrationKey.toLowerCase()];
      if (!featureKey) return true;
      return isFeatureEnabled(featureKey);
    },
    [isFeatureEnabled]
  );

  const enabledIntegrations = useMemo(() => {
    return Object.entries(INTEGRATION_FEATURES)
      .filter(([_, featureKey]) => isFeatureEnabled(featureKey))
      .map(([key]) => key);
  }, [isFeatureEnabled]);

  return { isIntegrationEnabled, enabledIntegrations };
}

/**
 * Hook to check sidebar segment visibility.
 */
export function useSidebarSegmentFeatures() {
  const { isFeatureEnabled } = useFeatureFlags();

  const isSegmentEnabled = useCallback(
    (segmentKey: string) =>
      isUIElementEnabled(segmentKey, SIDEBAR_SEGMENT_FEATURES, isFeatureEnabled),
    [isFeatureEnabled]
  );

  const enabledSegments = useMemo(() => {
    return Object.entries(SIDEBAR_SEGMENT_FEATURES)
      .filter(([_, features]) => {
        if (!features || features.length === 0) return true;
        return features.some((f) => isFeatureEnabled(f));
      })
      .map(([key]) => key);
  }, [isFeatureEnabled]);

  return { isSegmentEnabled, enabledSegments };
}

/**
 * Hook to check API operation availability.
 * Use before making API calls to prevent 403 errors.
 */
export function useAPIOperationFeatures() {
  const { isFeatureEnabled } = useFeatureFlags();

  const isOperationEnabled = useCallback(
    (operationKey: string) =>
      isUIElementEnabled(operationKey, API_OPERATION_FEATURES, isFeatureEnabled),
    [isFeatureEnabled]
  );

  const canExecute = useCallback(
    (operationKey: string): { allowed: boolean; requiredFeatures: string[] } => {
      const features = API_OPERATION_FEATURES[operationKey];
      
      if (!features || features.length === 0) {
        return { allowed: true, requiredFeatures: [] };
      }

      const featureList = Array.isArray(features) ? features : [features];
      const allowed = featureList.some((f) => isFeatureEnabled(f));
      
      return {
        allowed,
        requiredFeatures: allowed ? [] : featureList,
      };
    },
    [isFeatureEnabled]
  );

  return { isOperationEnabled, canExecute };
}

/**
 * Combined hook that provides all feature utilities.
 * Use this when you need multiple feature checks in one component.
 */
export function useAllFeatureUtils() {
  const { isFeatureEnabled, features, tierName, tierId } = useFeatureFlags();

  return {
    // Core
    isFeatureEnabled,
    features,
    tierName,
    tierId,

    // Specialized checkers
    settings: useSettingsSidebarFeatures(),
    flowToolbar: useFlowToolbarFeatures(),
    nodeToolbar: useNodeToolbarFeatures(),
    debug: useDebugFeatures(),
    integrations: useIntegrationFeatures(),
    sidebar: useSidebarSegmentFeatures(),
    api: useAPIOperationFeatures(),

    // Utility functions
    isUIElementEnabled: (key: string, map: FeatureMap) =>
      isUIElementEnabled(key, map, isFeatureEnabled),
    filterByFeatures: <T extends { key: string }>(items: T[], map: FeatureMap) =>
      filterByFeatures(items, map, isFeatureEnabled),
  };
}


