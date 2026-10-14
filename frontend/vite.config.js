import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // Read the backend address from a plain build variable named API_URL,
    // so it isn't exposed through Vite's VITE_ prefix. It is still baked
    // into the built JavaScript, which is fine: the browser must call it.
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.API_URL ?? ''),
  },
})
