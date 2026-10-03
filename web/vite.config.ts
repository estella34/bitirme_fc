import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Geliştirmede API'yi (FastAPI, :8000) aynı kökenden görmek için vekil sunucu.
const API = process.env.ENVANTER_API ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: API, ws: true, changeOrigin: true },
      "/media": { target: API, changeOrigin: true },
    },
  },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 1600,
  },
});
