import { defineConfig } from 'astro/config';

export default defineConfig({
  server: { host: true, port: 4321 },
  vite: {
    server: {
      proxy: {
        '/api': {
          target: process.env.API_URL || 'http://localhost:5000',
          changeOrigin: true,
        },
      },
    },
  },
});
