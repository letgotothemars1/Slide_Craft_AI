import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { LanguageProvider } from "@/context/LanguageContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import PublicOnlyRoute from "@/components/auth/PublicOnlyRoute";
import AdminRoute from "@/components/auth/AdminRoute";
import LandingPage from "./pages/LandingPage";
import GeneratePage from "./pages/GeneratePage";
import JobPage from "./pages/JobPage";
import AccountPage from "./pages/AccountPage";
import NotFound from "./pages/NotFound";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import TechDashboardPage from "./pages/TechDashboardPage";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <LanguageProvider>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route
                path="/auth"
                element={
                  <PublicOnlyRoute>
                    <AuthPage />
                  </PublicOnlyRoute>
                }
              />
              <Route
                path="/generate"
                element={
                  <ProtectedRoute>
                    <GeneratePage />
                  </ProtectedRoute>
                }
              />
              <Route path="/jobs/:jobId" element={<JobPage />} />
              <Route
                path="/dashboard"
                element={
                  <AdminRoute>
                    <DashboardPage />
                  </AdminRoute>
                }
              />
              <Route
                path="/tech-dashboard"
                element={
                  <AdminRoute>
                    <TechDashboardPage />
                  </AdminRoute>
                }
              />
              <Route
                path="/account"
                element={
                  <ProtectedRoute>
                    <AccountPage />
                  </ProtectedRoute>
                }
              />
              {/* History moved into the account page; old links still resolve. */}
              <Route path="/history" element={<Navigate to="/account" replace />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </LanguageProvider>
  </QueryClientProvider>
);

export default App;
