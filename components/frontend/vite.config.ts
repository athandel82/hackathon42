/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  // In live mode, point the dev proxy at a deployed/local API to keep
  // browser calls same-origin and avoid dev CORS (ARCHITECTURE.md §8.2).
  const apiTarget = env.VITE_API_BASE_URL || 'http://localhost:8080';

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/ingest': apiTarget,
        '/status': apiTarget,
        '/analyze': apiTarget,
      },
    },
    // Static-serve the production build on the EC2 VM (ARCHITECTURE.md §3).
    // Bind all interfaces and accept the public-DNS Host header.
    preview: {
      host: '0.0.0.0',
      port: 80,
      strictPort: true,
      allowedHosts: true,
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: false,
    },
  };
});
