import type { Users } from "@/types/api";

export interface AuthStoreType {
  isAdmin: boolean;
  isSuperAdmin: boolean;
  isTenantAdmin: boolean;
  tenantId: string | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  userData: Users | null;
  autoLogin: boolean | null;
  apiKey: string | null;
  authenticationErrorCount: number;

  setIsAdmin: (isAdmin: boolean) => void;
  setIsSuperAdmin: (isSuperAdmin: boolean) => void;
  setIsTenantAdmin: (isTenantAdmin: boolean) => void;
  setTenantId: (tenantId: string | null) => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  setAccessToken: (accessToken: string | null) => void;
  setUserData: (userData: Users | null) => void;
  setAutoLogin: (autoLogin: boolean) => void;
  setApiKey: (apiKey: string | null) => void;
  setAuthenticationErrorCount: (authenticationErrorCount: number) => void;
  logout: () => Promise<void>;
}
