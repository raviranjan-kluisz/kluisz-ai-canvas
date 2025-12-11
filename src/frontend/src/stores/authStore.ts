// authStore.ts - Multi-tenant authentication store

import { create } from "zustand";
import {
  KLUISZ_ACCESS_TOKEN,
  KLUISZ_API_TOKEN,
  KLUISZ_REFRESH_TOKEN,
} from "@/constants/constants";
import type { AuthStoreType } from "@/types/zustand/auth";
import { cookieManager, getCookiesInstance } from "@/utils/cookie-manager";

const cookies = getCookiesInstance();
const useAuthStore = create<AuthStoreType>((set, get) => ({
  isAdmin: false,
  isSuperAdmin: false,
  isTenantAdmin: false,
  tenantId: null,
  isAuthenticated: !!cookies.get(KLUISZ_ACCESS_TOKEN),
  accessToken: cookies.get(KLUISZ_ACCESS_TOKEN) ?? null,
  userData: null,
  autoLogin: null,
  apiKey: cookies.get(KLUISZ_API_TOKEN),
  authenticationErrorCount: 0,

  setIsAdmin: (isAdmin) => set({ isAdmin }),
  setIsSuperAdmin: (isSuperAdmin) => set({ isSuperAdmin }),
  setIsTenantAdmin: (isTenantAdmin) => set({ isTenantAdmin }),
  setTenantId: (tenantId) => set({ tenantId }),
  setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
  setAccessToken: (accessToken) => set({ accessToken }),
  setUserData: (userData) => {
    // Update role flags based on userData
    const isSuperAdmin = userData?.is_platform_superadmin ?? false;
    const isTenantAdmin = userData?.is_tenant_admin ?? false;
    const tenantId = userData?.tenant_id ?? null;
    // isAdmin is true for both super admin and tenant admin (for backward compatibility)
    const isAdmin = isSuperAdmin || isTenantAdmin;
    
    set({ 
      userData, 
      isAdmin,
      isSuperAdmin,
      isTenantAdmin,
      tenantId,
    });
  },
  setAutoLogin: (autoLogin) => set({ autoLogin }),
  setApiKey: (apiKey) => set({ apiKey }),
  setAuthenticationErrorCount: (authenticationErrorCount) =>
    set({ authenticationErrorCount }),

  logout: async () => {
    localStorage.removeItem(KLUISZ_ACCESS_TOKEN);
    localStorage.removeItem(KLUISZ_API_TOKEN);
    localStorage.removeItem(KLUISZ_REFRESH_TOKEN);

    cookieManager.clearAuthCookies();

    get().setIsAuthenticated(false);
    get().setIsAdmin(false);

    set({
      isAdmin: false,
      isSuperAdmin: false,
      isTenantAdmin: false,
      tenantId: null,
      userData: null,
      accessToken: null,
      isAuthenticated: false,
      autoLogin: false,
      apiKey: null,
    });
  },
}));

export default useAuthStore;
