import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

interface Props {
  children: React.ReactNode;
}

/**
 * Route guard for admin-only pages (dashboards).
 *
 * Three outcomes:
 *   1. Session is still loading → render a tiny placeholder.
 *   2. User is not logged in → bounce to /auth with "from" state so the
 *      login page can redirect back after success.
 *   3. User is logged in but not admin → bounce to home with an explanatory
 *      message in route state (LandingPage can show a toast if desired).
 */
export default function AdminRoute({ children }: Props) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-muted-foreground">
        Проверяем сессию…
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace state={{ from: location.pathname }} />;
  }

  if (!isAdmin) {
    return (
      <Navigate
        to="/"
        replace
        state={{ reason: "admin-required", from: location.pathname }}
      />
    );
  }

  return <>{children}</>;
}
