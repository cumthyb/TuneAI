import { readFileSync, existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(__dirname, '..')

function loadAppConfig(): { devPort: number; apiTarget: string } {
  for (const name of ['config.json', 'config.example.json']) {
    const p = path.join(projectRoot, name)
    if (!existsSync(p)) continue
    try {
      const raw = readFileSync(p, 'utf-8')
      const cfg = JSON.parse(raw) as Record<string, unknown>
      const server = (cfg.server ?? {}) as Record<string, unknown>
      const frontend = (cfg.frontend ?? {}) as Record<string, unknown>
      const port = Number(frontend.dev_port) || 5173
      const backendPort = Number(server.port) || 8000
      const host = typeof server.host === 'string' ? server.host : '0.0.0.0'
      const apiTarget =
        host === '0.0.0.0' || host === '::'
          ? `http://127.0.0.1:${backendPort}`
          : `http://${host}:${backendPort}`
      return { devPort: port, apiTarget }
    } catch {
      continue
    }
  }
  return { devPort: 5173, apiTarget: 'http://127.0.0.1:8000' }
}

const { devPort, apiTarget } = loadAppConfig()

export default defineConfig({
  plugins: [react()],
  root: '.',
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler',
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: devPort,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})
