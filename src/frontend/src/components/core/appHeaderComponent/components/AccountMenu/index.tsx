import { ForwardedIconComponent } from "@/components/common/genericIconComponent";
import {
  DATASTAX_DOCS_URL,
  DOCS_URL,
  TWITTER_URL,
} from "@/constants/constants";
import { useLogout } from "@/controllers/API/queries/auth";
import { CustomProfileIcon } from "@/customization/components/custom-profile-icon";
import { ENABLE_DATASTAX_KLUISZ } from "@/customization/feature-flags";
import { useCustomNavigate } from "@/customization/hooks/use-custom-navigate";
import useAuthStore from "@/stores/authStore";
import { useDarkStore } from "@/stores/darkStore";
import { cn, stripReleaseStageFromVersion } from "@/utils/utils";
import {
  HeaderMenu,
  HeaderMenuItemButton,
  HeaderMenuItemLink,
  HeaderMenuItems,
  HeaderMenuToggle,
} from "../HeaderMenu";
import ThemeButtons from "../ThemeButtons";

export const AccountMenu = () => {
  const version = useDarkStore((state) => state.version);
  const latestVersion = useDarkStore((state) => state.latestVersion);
  const navigate = useCustomNavigate();
  const { mutate: mutationLogout } = useLogout();

  const { isAdmin, isSuperAdmin, isTenantAdmin, autoLogin } = useAuthStore((state) => ({
    isAdmin: state.isAdmin,
    isSuperAdmin: state.isSuperAdmin,
    isTenantAdmin: state.isTenantAdmin,
    autoLogin: state.autoLogin,
  }));

  const handleLogout = () => {
    mutationLogout();
  };

  const isLatestVersion = (() => {
    if (!version || !latestVersion) return false;

    const currentBaseVersion = stripReleaseStageFromVersion(version);
    const latestBaseVersion = stripReleaseStageFromVersion(latestVersion);

    return currentBaseVersion === latestBaseVersion;
  })();

  return (
    <HeaderMenu>
      <HeaderMenuToggle>
        <div
          className="h-6 w-6 rounded-lg focus-visible:outline-0"
          data-testid="user-profile-settings"
        >
          <CustomProfileIcon />
        </div>
      </HeaderMenuToggle>
      <HeaderMenuItems position="right" classNameSize="w-[272px]">
        <div className="divide-y divide-foreground/10">
          <div>
            <div className="h-[44px] items-center px-4 pt-3">
              <div className="flex items-center justify-between">
                <span
                  data-testid="menu_version_button"
                  id="menu_version_button"
                  className="text-sm"
                >
                  Version
                </span>
                <div
                  className={cn(
                    "float-right text-xs",
                    isLatestVersion && "text-accent-emerald-foreground",
                    !isLatestVersion && "text-accent-amber-foreground",
                  )}
                >
                  {version}{" "}
                  {isLatestVersion ? "(latest)" : "(update available)"}
                </div>
              </div>
            </div>
          </div>

          <div>
            <HeaderMenuItemButton
              onClick={() => {
                navigate("/my-usage");
              }}
            >
              <span
                data-testid="menu_my_usage_button"
                id="menu_my_usage_button"
              >
                My Usage
              </span>
            </HeaderMenuItemButton>
            <HeaderMenuItemButton
              onClick={() => {
                navigate("/settings");
              }}
            >
              <span
                data-testid="menu_settings_button"
                id="menu_settings_button"
              >
                Settings
              </span>
            </HeaderMenuItemButton>

            {/* Super Admin can access all admin pages */}
            {isSuperAdmin && !autoLogin && (
              <div>
                <HeaderMenuItemButton
                  onClick={() => {
                    navigate("/super-admin");
                  }}
                >
                  <span
                    data-testid="menu_super_admin_button"
                    id="menu_super_admin_button"
                  >
                    Platform Admin
                  </span>
                </HeaderMenuItemButton>
              </div>
            )}
            {/* Tenant Admin and Super Admin can access tenant admin page */}
            {(isTenantAdmin || isSuperAdmin) && !autoLogin && (
              <div>
                <HeaderMenuItemButton
                  onClick={() => {
                    navigate("/admin/tenant");
                  }}
                >
                  <span
                    data-testid="menu_tenant_admin_button"
                    id="menu_tenant_admin_button"
                  >
                    Organization Admin
                  </span>
                </HeaderMenuItemButton>
              </div>
            )}
            {/* Legacy admin page for backward compatibility */}
            {isAdmin && !autoLogin && (
              <div>
                <HeaderMenuItemButton
                  onClick={() => {
                    navigate("/admin");
                  }}
                >
                  <span
                    data-testid="menu_admin_page_button"
                    id="menu_admin_page_button"
                  >
                    User Management
                  </span>
                </HeaderMenuItemButton>
              </div>
            )}
            <HeaderMenuItemLink
              newPage
              href={ENABLE_DATASTAX_KLUISZ ? DATASTAX_DOCS_URL : DOCS_URL}
            >
              <span data-testid="menu_docs_button" id="menu_docs_button">
                Docs
              </span>
            </HeaderMenuItemLink>
          </div>

          <div>
            <HeaderMenuItemLink newPage href={TWITTER_URL}>
              <span
                data-testid="menu_twitter_button"
                id="menu_twitter_button"
                className="flex items-center gap-2"
              >
                <ForwardedIconComponent
                  strokeWidth={2}
                  name="TwitterX"
                  className="h-4 w-4"
                />
                X
              </span>
            </HeaderMenuItemLink>
          </div>

          <div className="flex items-center justify-between px-4 py-[6.5px] text-sm">
            <span className="">Theme</span>
            <div className="relative top-[1px] float-right">
              <ThemeButtons />
            </div>
          </div>

          {!autoLogin && (
            <div>
              <HeaderMenuItemButton onClick={handleLogout} icon="log-out">
                Logout
              </HeaderMenuItemButton>
            </div>
          )}
        </div>
      </HeaderMenuItems>
    </HeaderMenu>
  );
};
