import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    allowedHosts: true,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/auth/login": "http://127.0.0.1:8000",
      "/auth/signup": "http://127.0.0.1:8000",
      "/auth/me": "http://127.0.0.1:8000",
      "/generate": {
        target: "http://127.0.0.1:8000",
        bypass: (req) => req.method === "GET" ? req.url : undefined,
      },
      "/projects": {
        target: "http://127.0.0.1:8000",
        bypass: (req) => req.headers.accept?.includes("text/html") ? req.url : undefined,
      },
      "/documents": "http://127.0.0.1:8000",
      "/status": "http://127.0.0.1:8000",
      "/files": "http://127.0.0.1:8000",
      "/metrics": "http://127.0.0.1:8000",
      "/events": "http://127.0.0.1:8000",
    },
    hmr: {
      overlay: false,
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
