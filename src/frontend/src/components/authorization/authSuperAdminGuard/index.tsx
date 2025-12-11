import { useContext } from "react";
import { AuthContext } from "@/contexts/authContext";
import { CustomNavigate } from "@/customization/components/custom-navigate";
import { LoadingPage } from "@/pages/LoadingPage";
import useAuthStore from "@/stores/authStore";

export const ProtectedSuperAdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { userData } = useContext(AuthContext);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const isSuperAdmin = useAuthStore((state) => state.isSuperAdmin);

  if (!isAuthenticated) {
    return <LoadingPage />;
  } else if ((userData && !isSuperAdmin) || autoLogin) {
    // Redirect non-super-admins to home
    return <CustomNavigate to="/" replace />;
  } else {
    return children;
  }
};

