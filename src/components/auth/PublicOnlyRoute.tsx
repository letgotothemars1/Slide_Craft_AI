import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

interface Props {
  children: React.ReactNode;
}

export default function PublicOnlyRoute({ children }: Props) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-muted-foreground">
        Проверяем сессию…
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/generate" replace />;
  }

  return <>{children}</>;
}
