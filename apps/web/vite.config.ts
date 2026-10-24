import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), {
    name: "fe-p1-heavy-dependency-map",
    generateBundle(_options, bundle) {
      const heavyByChunk: Record<string, string[]> = {};
      for (const asset of Object.values(bundle)) {
        if (asset.type !== "chunk") continue;
        const modules = Object.keys(asset.modules).map((id) => id.replaceAll("\\", "/"));
        const heavy = [
          modules.some((id) => id.includes("/node_modules/@tiptap/") || id.includes("/node_modules/tiptap-markdown/")) ? "TipTap" : null,
        ].filter((name): name is string => name !== null);
        if (heavy.length) heavyByChunk[asset.fileName] = heavy;
      }
      this.emitFile({ type: "asset", fileName: "heavy-dependencies.json", source: JSON.stringify(heavyByChunk) });
    },
  }],
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.AI_STUDIO_API_TARGET || "http://localhost:8000",
    },
  },
});
