import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // Proxy API calls to the backend during local dev (npm run dev)
    proxy: {
      "/ws": { target: "ws://localhost:8000", ws: true },
      "/roi": { target: "http://localhost:8000" },
      "/health": { target: "http://localhost:8000" },
    },
  },
});
