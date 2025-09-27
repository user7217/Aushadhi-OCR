import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const API = env.VITE_API_BASE_URL || "http://localhost:8000";
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/infer": {
          target: API,
          changeOrigin: true,
          secure: false
        }
      }
    },
    build: {
      outDir: "dist"
    }
  };
});
