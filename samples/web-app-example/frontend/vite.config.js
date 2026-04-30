import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const nurieProxyTarget =
    env.VITE_NURIE_PROXY_TARGET || 'https://api.vault.nurie.ai'
  // 127.0.0.1 avoids some macOS setups where `localhost` resolves to ::1 first and the proxy
  // misses a server bound only on IPv4.
  const localBackend =
    env.VITE_BACKEND_PROXY_TARGET || 'http://127.0.0.1:8000'

  const toBackend = { target: localBackend, changeOrigin: true }

  const proxy = {
    // Same-origin /api/v1/... during `npm run dev` / `vite preview` (direct Nurie mode).
    '/api': {
      target: nurieProxyTarget,
      changeOrigin: true,
    },
    // Longer prefix first so `/nurie/vault/...` always hits the backend proxy rule.
    '/nurie/vault': toBackend,
    '/nurie': toBackend,
  }

  return {
    plugins: [vue()],
    // `vite preview` does not inherit `server.proxy` — without this, POST /nurie/... → 404.
    server: { proxy },
    preview: { proxy },
  }
})
