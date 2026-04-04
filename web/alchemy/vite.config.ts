import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  base: '/static/alchemy-dist/',
  build: {
    outDir: path.resolve(__dirname, '../static/alchemy-dist'),
    emptyDirBeforeWrite: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    },
  },
});
