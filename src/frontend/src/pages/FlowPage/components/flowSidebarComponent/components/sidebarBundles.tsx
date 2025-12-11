import { memo, useMemo } from "react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
} from "@/components/ui/sidebar";
import { BUNDLE_FEATURES, normalizeBundleName } from "@/constants/feature-maps";
import { useFeatureFlags } from "@/contexts/featureContext";
import { ENABLE_NEW_SIDEBAR } from "@/customization/feature-flags";
import type { SidebarGroupProps } from "../types";
import { BundleItem } from "./bundleItems";
import { SearchConfigTrigger } from "./searchConfigTrigger";

export const MemoizedSidebarGroup = memo(
  ({
    BUNDLES,
    search,
    sortedCategories,
    dataFilter,
    nodeColors,
    onDragStart,
    sensitiveSort,
    handleKeyDownInput,
    openCategories,
    setOpenCategories,
    showSearchConfigTrigger,
    showConfig,
    setShowConfig,
  }: SidebarGroupProps) => {
    const { isFeatureEnabled } = useFeatureFlags();
    
    const sortedBundles = useMemo(() => {
      return BUNDLES.toSorted((a, b) => {
        const referenceArray = search !== "" ? sortedCategories : BUNDLES;
        return (
          referenceArray.findIndex((value) => value === a.name) -
          referenceArray.findIndex((value) => value === b.name)
        );
      }).filter((item: { name: string | number }) => {
        // First check if bundle has data
        if (!dataFilter[item.name] || Object.keys(dataFilter[item.name]).length === 0) {
          return false;
        }
        
        // Then check feature flag for this bundle (external integrations)
        const bundleName = String(item.name);
        const normalizedName = normalizeBundleName(bundleName);
        const featureKey = BUNDLE_FEATURES[normalizedName];
        
        // Only show bundles that have feature flags defined in the registry
        // If no feature key defined, hide the bundle (controlled from license tier only)
        if (!featureKey) return false;
        
        // Check if the feature is enabled for the current user's tier
        return isFeatureEnabled(featureKey);
      });
    }, [BUNDLES, search, sortedCategories, dataFilter, isFeatureEnabled]);

    return (
      <SidebarGroup className="p-3 pr-2">
        <SidebarGroupLabel className="cursor-default w-full flex items-center justify-between">
          <span>Bundles</span>
          {showSearchConfigTrigger && ENABLE_NEW_SIDEBAR && (
            <SearchConfigTrigger
              showConfig={showConfig}
              setShowConfig={setShowConfig}
            />
          )}
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {sortedBundles.map((item) => (
              <BundleItem
                key={item.name}
                item={item}
                openCategories={openCategories}
                setOpenCategories={setOpenCategories}
                dataFilter={dataFilter}
                nodeColors={nodeColors}
                onDragStart={onDragStart}
                sensitiveSort={sensitiveSort}
                handleKeyDownInput={handleKeyDownInput}
              />
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  },
);

MemoizedSidebarGroup.displayName = "MemoizedSidebarGroup";

export default MemoizedSidebarGroup;
