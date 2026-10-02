import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // dev mode: proxy API calls to the app tier
    // (kubectl port-forward svc/app 8000:8000)
    proxy: { '/api': 'http://localhost:8000' },
  },
})
