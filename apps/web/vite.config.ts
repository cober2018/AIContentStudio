import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.AI_STUDIO_API_TARGET || "http://localhost:8000",
    },
  },
});
