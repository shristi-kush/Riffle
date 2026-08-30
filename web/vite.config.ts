import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The SPA build outputs to web/dist, which FastAPI serves as static files.
// In dev, API paths are proxied to the local FastAPI process so relative
// fetches work without configuring VITE_API_BASE.
const API_TARGET = "http://localhost:5000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      [
        "/health",
        "/ingest",
        "/chat",
        "/voice-chat",
        "/corpus",
        "/reset",
        "/docs",
        "/openapi.json",
      ].map(
        (path) => [path, { target: API_TARGET, changeOrigin: true }]
      )
    ),
  },
  build: {
    outDir: "dist",
  },
});
