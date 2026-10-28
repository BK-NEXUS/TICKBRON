import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Tunnels (ngrok) that may open the dev and preview servers; Vite refuses other host names
const TUNNEL_HOSTS = ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app', '.ngrok.dev', '.ngrok.io']

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    allowedHosts: TUNNEL_HOSTS,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Hotel photos come as /media/... paths; the API server serves them in development
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    allowedHosts: TUNNEL_HOSTS,
  },
  build: {
    // Enable source maps for production debugging
    sourcemap: false,
    // Optimize chunk size warning threshold
    chunkSizeWarningLimit: 1000,
    // Rollup options for bundle optimization
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return undefined
          if (/node_modules\/(react|react-dom|react-router|react-router-dom|scheduler)\//.test(id)) return 'react-vendor'
          if (id.includes('node_modules/react-helmet-async/')) return 'ui-vendor'
          return undefined
        },
      },
    },
  },
  // Optimize dependencies
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'react-helmet-async'],
  },
})
