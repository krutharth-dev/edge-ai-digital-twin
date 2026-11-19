import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy API/WebSocket to local FastAPI; no frontend secrets or hard-coded cloud URLs.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000" },
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});
