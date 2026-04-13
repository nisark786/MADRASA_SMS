import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  build: {
    // Optimization strategies
    rollupOptions: {
      output: {
        // Advanced code splitting strategy
        manualChunks(id) {
          // Vendor chunks for better caching
          if (id.includes('node_modules/react')) {
            return 'vendor-react'
          }
          if (id.includes('node_modules/react-router-dom')) {
            return 'vendor-react'
          }
          if (id.includes('node_modules/react-dom')) {
            return 'vendor-react'
          }
          if (id.includes('node_modules/lucide-react')) {
            return 'vendor-ui'
          }
          if (id.includes('node_modules/zustand')) {
            return 'vendor-state'
          }
          if (id.includes('node_modules/axios')) {
            return 'vendor-http'
          }
          // OpenTelemetry as separate chunk
          if (id.includes('node_modules/@opentelemetry')) {
            return 'vendor-otel'
          }
          // Pages as separate chunks for route-level code splitting
          if (id.includes('/pages/')) {
            const pageName = id.split('/pages/')[1].split('.')[0]
            return `page-${pageName}`
          }
        },
        chunkFileNames: 'chunks/[name].[hash].js',
        entryFileNames: '[name].[hash].js',
        assetFileNames: 'assets/[name].[hash][extname]'
      }
    },
    // Aggressive minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: true,
        passes: 2,  // Multiple passes for better compression
      },
      mangle: true,
      format: {
        comments: false
      }
    },
    // Optimize source maps
    sourcemap: false,
    // Modern browser target for smaller output
    target: 'es2020',
    // CSS code splitting for critical rendering path
    cssCodeSplit: true,
    // Increase chunk size warning
    chunkSizeWarningLimit: 500,
    // Disable brotli to speed up build
    brotliSize: false,
    // Increase timeout for large apps
    assetsInlineLimit: 4096,
    // Enable gzip preview
    reportCompressedSize: false,
  },
  
  // Development server optimization
  server: {
    compression: 'gzip',
    // Enable warm asset server for faster HMR
    middlewareMode: false,
  },
  
  // Optimization hints
  resolve: {
    alias: {
      // Optional: add aliases for shorter imports
      // '@': '/src',
      // '@components': '/src/components',
      // '@pages': '/src/pages',
      // '@store': '/src/store',
      // '@api': '/src/api',
    }
  }
})
