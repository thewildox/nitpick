import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // any request starting with /api gets forwarded to your FastAPI backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // strip the /api prefix: /api/runs → /runs
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})