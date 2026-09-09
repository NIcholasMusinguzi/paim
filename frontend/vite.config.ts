import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // Offline capability is IndexedDB (the agent outbox), not cached API
    // responses — this only precaches the app shell so it still loads with
    // no network (section 8: agent devices need to work with no signal).
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: "auto",
      manifest: {
        name: "PAIM",
        short_name: "PAIM",
        start_url: "/agent",
        display: "standalone",
        background_color: "#eef3ea",
        theme_color: "#0f3d2e",
      },
      workbox: { navigateFallbackDenylist: [/^\/api\//, /^\/ws\//] },
    }),
  ],
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("recharts") || id.includes("d3-")) return "charts";
          if (id.includes("dexie")) return "offline";
          if (id.includes("react-dom") || id.includes("react-router") || id.includes("@tanstack")) return "vendor";
        },
      },
    },
  },
});
