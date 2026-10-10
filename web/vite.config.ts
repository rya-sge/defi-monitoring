import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The FastAPI backend lives at 127.0.0.1:8000 and serves everything under /api,
// including the Server-Sent Events stream at /api/watch/stream (hence no buffering).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
