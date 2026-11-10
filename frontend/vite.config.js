import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true })],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    // En desarrollo, /api va al backend Django: mismo origen, sin problemas de cookies.
    proxy: {
      // 127.0.0.1 y no "localhost": en Windows, Node resuelve localhost a IPv6 (::1)
      // y runserver escucha en IPv4, lo que da 502 Bad Gateway.
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/admin': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    server: { deps: { inline: ['vuetify'] } },
  },
})
