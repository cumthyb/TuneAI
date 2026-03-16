import { readFileSync, existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(__dirname, '..')

function loadAppConfig(): { devPort: number; apiTarget: string } {
  const p = path.join(projectRoot, 'config.json')
  if (!existsSync(p)) {
    throw new Error(`Missing required config file: ${p}`)
  }
  const raw = readFileSync(p, 'utf-8')
  const cfg = JSON.parse(raw) as Record<string, unknown>
  const server = cfg.server
  const frontend = cfg.frontend
  if (!server || typeof server !== 'object') {
    throw new Error('config.server must be an object')
  }
  if (!frontend || typeof frontend !== 'object') {
    throw new Error('config.frontend must be an object')
  }
  const serverCfg = server as Record<string, unknown>
  const frontendCfg = frontend as Record<string, unknown>
  const host = serverCfg.host
  const backendPort = serverCfg.port
  const devPort = frontendCfg.dev_port
  if (typeof host !== 'string' || host.trim().length === 0) {
    throw new Error('config.server.host must be a non-empty string')
  }
  if (typeof backendPort !== 'number' || !Number.isInteger(backendPort) || backendPort <= 0) {
    throw new Error('config.server.port must be a positive integer')
  }
  if (typeof devPort !== 'number' || !Number.isInteger(devPort) || devPort <= 0) {
    throw new Error('config.frontend.dev_port must be a positive integer')
  }
  const apiTarget =
    host === '0.0.0.0' || host === '::'
      ? `http://127.0.0.1:${backendPort}`
      : `http://${host}:${backendPort}`
  return { devPort, apiTarget }
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
