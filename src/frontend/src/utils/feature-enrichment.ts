/**
 * Feature Enrichment Utilities
 * 
 * Automatically enriches component types with feature_key metadata
 * based on component name and category. This makes filtering automatic
 * without requiring backend changes.
 * 
 * @see docs/dev/tenant-features/EXTENSIBILITY_GUIDE.md
 */

import {
  COMPONENT_TYPE_FEATURES,
  COMPONENT_CATEGORY_FEATURES,
  PROVIDER_FEATURE_MAP,
} from "@/constants/feature-maps";
import type { APIClassType, APIDataType } from "@/types/api";

/**
 * Detects the model provider from a component name or type.
 */
function detectProviderFromName(name: string): string | null {
  const nameLower = name.toLowerCase();
  
  for (const [provider] of Object.entries(PROVIDER_FEATURE_MAP)) {
    if (nameLower.includes(provider.toLowerCase())) {
      return provider;
    }
  }
  
  // Special cases
  if (nameLower.includes("gpt") || nameLower.includes("openai")) return "openai";
  if (nameLower.includes("claude")) return "anthropic";
  if (nameLower.includes("gemini")) return "google";
  if (nameLower.includes("llama") && nameLower.includes("ollama")) return "ollama";
  if (nameLower.includes("mistral")) return "mistral";
  if (nameLower.includes("bedrock")) return "aws_bedrock";
  if (nameLower.includes("azure") && nameLower.includes("openai")) return "azure_openai";
  if (nameLower.includes("groq")) return "groq";
  
  return null;
}

/**
 * Determines the feature_key for a component based on its name and category.
 */
export function getComponentFeatureKey(
  componentName: string,
  category?: string,
  displayName?: string,
): string | null {
  // 1. Check explicit mapping first
  const explicitKey = COMPONENT_TYPE_FEATURES[componentName] || 
                      (displayName && COMPONENT_TYPE_FEATURES[displayName]);
  if (explicitKey) return explicitKey;
  
  // 2. Check if it's a model component
  const provider = detectProviderFromName(componentName) || 
                   (displayName && detectProviderFromName(displayName));
  if (provider) {
    return PROVIDER_FEATURE_MAP[provider] || `models.${provider}`;
  }
  
  // 3. Check category-based feature
  if (category) {
    const categoryKey = COMPONENT_CATEGORY_FEATURES[category];
    if (categoryKey) return categoryKey;
  }
  
  // 4. Special component types
  const nameLower = componentName.toLowerCase();
  if (nameLower.includes("mcp")) return "integrations.mcp";
  if (nameLower.includes("custom") && nameLower.includes("component")) {
    return "components.custom.enabled";
  }
  // NOTE: All observability (langfuse, langsmith, langwatch) is mandatory/always-on
  
  // Vector stores
  if (nameLower.includes("chroma")) return "integrations.vector_stores.chroma";
  if (nameLower.includes("pinecone")) return "integrations.vector_stores.pinecone";
  if (nameLower.includes("qdrant")) return "integrations.vector_stores.qdrant";
  if (nameLower.includes("weaviate")) return "integrations.vector_stores.weaviate";
  if (nameLower.includes("milvus")) return "integrations.vector_stores.milvus";
  
  return null;
}

/**
 * Enriches a single component type with feature_key metadata.
 */
export function enrichComponentWithFeatureKey<T extends APIClassType>(
  component: T,
  componentName: string,
  category?: string,
): T & { feature_key?: string } {
  const featureKey = getComponentFeatureKey(
    componentName,
    category,
    component.display_name,
  );
  
  if (featureKey) {
    return { ...component, feature_key: featureKey };
  }
  
  return component;
}

/**
 * Enriches all components in a category with feature_key metadata.
 */
export function enrichCategoryComponents(
  components: Record<string, APIClassType>,
  category: string,
): Record<string, APIClassType & { feature_key?: string }> {
  const enriched: Record<string, APIClassType & { feature_key?: string }> = {};
  
  for (const [name, component] of Object.entries(components)) {
    enriched[name] = enrichComponentWithFeatureKey(component, name, category);
  }
  
  return enriched;
}

/**
 * Enriches all component data with feature_key metadata.
 * Use this when loading components from the API.
 */
export function enrichAllComponentsWithFeatureKeys(
  data: APIDataType,
): APIDataType {
  const enriched: APIDataType = {};
  
  for (const [category, components] of Object.entries(data)) {
    enriched[category] = enrichCategoryComponents(components, category);
  }
  
  return enriched;
}

/**
 * Gets the required features for a list of component names.
 * Useful for validating flow execution.
 */
export function getRequiredFeaturesForComponents(
  componentNames: string[],
): string[] {
  const features = new Set<string>();
  
  for (const name of componentNames) {
    const featureKey = getComponentFeatureKey(name);
    if (featureKey) {
      features.add(featureKey);
    }
  }
  
  return Array.from(features);
}

export default {
  getComponentFeatureKey,
  enrichComponentWithFeatureKey,
  enrichCategoryComponents,
  enrichAllComponentsWithFeatureKeys,
  getRequiredFeaturesForComponents,
};


