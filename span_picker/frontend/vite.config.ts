import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./",              // ⭐关键：相对路径，Streamlit 组件必须
  build: {
    outDir: "dist",        // ✅ 保留（默认其实也是 dist，但留着更清晰）
  },
});
