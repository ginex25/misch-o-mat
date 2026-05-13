import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/liquids': 'http://localhost:5000',
      '/drinks': 'http://localhost:5000',
      '/update': 'http://localhost:5000',
      '/preparation': 'http://localhost:5000',
      '/shutdown': 'http://localhost:5000',
      '/calibrate': 'http://localhost:5000',
      '/clean': 'http://localhost:5000',
      '/reset': 'http://localhost:5000',
      '/tare': 'http://localhost:5000',
    }
  }
})