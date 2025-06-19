import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,  // optional, defaults to 5173 anyway
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // 🔁 update this to match your FastAPI port
        changeOrigin: true,
      },
    },
  },
})
