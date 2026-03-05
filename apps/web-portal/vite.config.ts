import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // /api/v1/verify → /verify
        rewrite: (path) => path.replace(/^\/api\/v1/, ''),
      },
    },
  },
});
