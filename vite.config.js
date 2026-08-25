import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      'gratitude-gumball-wince.ngrok-free.dev',
    ],
  },
})