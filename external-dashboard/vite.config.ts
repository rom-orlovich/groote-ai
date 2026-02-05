import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
      },
      "/oauth": {
        target: "http://localhost:8010",
        changeOrigin: true,
      },
      "/webhooks": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "http://localhost:5001",
        ws: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
