import { useContext } from "react";
import { AuthContext } from "@/contexts/authContext";
import { CustomNavigate } from "@/customization/components/custom-navigate";
import { LoadingPage } from "@/pages/LoadingPage";
import useAuthStore from "@/stores/authStore";

export const ProtectedTenantAdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { userData } = useContext(AuthContext);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const isSuperAdmin = useAuthStore((state) => state.isSuperAdmin);
  const isTenantAdmin = useAuthStore((state) => state.isTenantAdmin);

  // Super admins can also access tenant admin pages
  const hasAccess = isSuperAdmin || isTenantAdmin;

  if (!isAuthenticated) {
    return <LoadingPage />;
  } else if ((userData && !hasAccess) || autoLogin) {
    // Redirect users without admin access to home
    return <CustomNavigate to="/" replace />;
  } else {
    return children;
  }
};

