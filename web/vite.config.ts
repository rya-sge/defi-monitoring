import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// The FastAPI backend lives at 127.0.0.1:8000 and serves everything under /api,
// including the Server-Sent Events stream at /api/watch/stream (hence no buffering).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  server: {
    // 127.0.0.1, not localhost (which may bind ::1 only): Caddy proxies belem.fuca.ch here.
    host: '127.0.0.1',
    port: 5173,
    allowedHosts: ['belem.fuca.ch'],
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
