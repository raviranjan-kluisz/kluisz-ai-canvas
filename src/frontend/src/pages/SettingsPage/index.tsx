import { useMemo } from "react";
import { Outlet, type To } from "react-router-dom";
import SideBarButtonsComponent from "@/components/core/sidebarComponent";
import { SidebarProvider } from "@/components/ui/sidebar";
import { CustomStoreSidebar } from "@/customization/components/custom-store-sidebar";
import {
  ENABLE_DATASTAX_KLUISZ,
  ENABLE_KLUISZ_STORE,
  ENABLE_PROFILE_ICONS,
} from "@/customization/feature-flags";
import useAuthStore from "@/stores/authStore";
import { useStoreStore } from "@/stores/storeStore";
import { useSettingsSidebarFeatures } from "@/hooks/features";
import ForwardedIconComponent from "../../components/common/genericIconComponent";
import PageLayout from "../../components/common/pageLayout";

export default function SettingsPage(): JSX.Element {
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const hasStore = useStoreStore((state) => state.hasStore);
  
  // Use the centralized settings sidebar feature check
  // This uses SETTINGS_SIDEBAR_FEATURES from feature-maps.ts
  const { isItemEnabled } = useSettingsSidebarFeatures();

  // Hides the General settings if there is nothing to show
  const showGeneralSettings = ENABLE_PROFILE_ICONS || hasStore || !autoLogin;

  // Build sidebar items with feature-based filtering
  const sidebarNavItems = useMemo(() => {
    const items: {
      href?: string;
      title: string;
      icon: React.ReactNode;
      key?: string;
    }[] = [];

    if (showGeneralSettings) {
      items.push({
        key: "general",
        title: "General",
        href: "/settings/general",
        icon: (
          <ForwardedIconComponent
            name="SlidersHorizontal"
            className="w-4 flex-shrink-0 justify-start stroke-[1.5]"
          />
        ),
      });
    }

    // MCP Servers - gated by feature flag via feature-maps.ts
    if (isItemEnabled("mcp-servers")) {
      items.push({
        key: "mcp-servers",
        title: "MCP Servers",
        href: "/settings/mcp-servers",
        icon: (
          <ForwardedIconComponent
            name="Mcp"
            className="w-4 flex-shrink-0 justify-start stroke-[1.5]"
          />
        ),
      });
    }

    // Global Variables - gated by feature flag via feature-maps.ts
    if (isItemEnabled("global-variables")) {
      items.push({
        key: "global-variables",
        title: "Global Variables",
        href: "/settings/global-variables",
        icon: (
          <ForwardedIconComponent
            name="Globe"
            className="w-4 flex-shrink-0 justify-start stroke-[1.5]"
          />
        ),
      });
    }

    // Shortcuts - Always visible (core functionality)
    items.push({
      key: "shortcuts",
      title: "Shortcuts",
      href: "/settings/shortcuts",
      icon: (
        <ForwardedIconComponent
          name="Keyboard"
          className="w-4 flex-shrink-0 justify-start stroke-[1.5]"
        />
      ),
    });

    // Messages - gated by feature flag via feature-maps.ts
    if (isItemEnabled("messages")) {
      items.push({
        key: "messages",
        title: "Messages",
        href: "/settings/messages",
        icon: (
          <ForwardedIconComponent
            name="MessagesSquare"
            className="w-4 flex-shrink-0 justify-start stroke-[1.5]"
          />
        ),
      });
    }

    // API Keys - gated by feature flag via feature-maps.ts
    if (!ENABLE_DATASTAX_KLUISZ && isItemEnabled("api-keys")) {
      const kluiszItems = CustomStoreSidebar(true, ENABLE_KLUISZ_STORE);
      items.splice(2, 0, ...kluiszItems.map(item => ({ ...item, key: item.href })));
    }

    return items;
  }, [showGeneralSettings, isItemEnabled]);

  return (
    <PageLayout
      backTo={-1 as To}
      title="Settings"
      description="Manage the general settings for Kluisz Kanvas."
    >
      <SidebarProvider width="15rem" defaultOpen={false}>
        <SideBarButtonsComponent items={sidebarNavItems} />
        <main className="flex flex-1 overflow-hidden">
          <div className="flex flex-1 flex-col overflow-x-hidden pt-1">
            <Outlet />
          </div>
        </main>
      </SidebarProvider>
    </PageLayout>
  );
}
