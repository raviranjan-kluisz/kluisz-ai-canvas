/**
 * Feature Hooks - Centralized exports for feature-related hooks.
 * 
 * These hooks implement the metadata-driven feature gating patterns
 * described in the Extensibility Guide.
 * 
 * @see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md
 */

// Model filtering
export {
  useFilteredModels,
  useEnabledProviders,
  useIsProviderEnabled,
  useFilteredModelsRecord,
  type BaseModel,
} from "./use-filtered-models";

// Component filtering
export {
  useFilteredComponents,
  useFilteredComponentsByCategory,
  useIsCategoryEnabled,
  useIsComponentTypeEnabled,
  useEnabledCategories,
  type FeatureAwareComponent,
} from "./use-filtered-components";

// Feature utilities
export {
  isUIElementEnabled,
  filterByFeatures,
  useSettingsSidebarFeatures,
  useFlowToolbarFeatures,
  useNodeToolbarFeatures,
  useDebugFeatures,
  useIntegrationFeatures,
  useSidebarSegmentFeatures,
  useAPIOperationFeatures,
  useAllFeatureUtils,
} from "./use-feature-utils";


