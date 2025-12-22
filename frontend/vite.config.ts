import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173 },
  // Support for subpath deployment (e.g., /mordoc) via Traefik
  base: process.env.VITE_BASE || '/',
})
