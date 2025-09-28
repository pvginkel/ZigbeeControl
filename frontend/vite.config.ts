import fs from 'node:fs'
import path from 'node:path'
import { defineConfig, loadEnv, type ProxyOptions } from 'vite'
import { parse } from 'yaml'
import react from '@vitejs/plugin-react'

interface RawTabConfig {
  iframeUrl?: string
  proxyTarget?: string
}

interface RawAppConfig {
  tabs?: RawTabConfig[]
}

function normalizeBasePath(input: string): string | null {
  const trimmed = input.trim()
  if (!trimmed) {
    return null
  }

  const withLeadingSlash = trimmed.startsWith('/') ? trimmed : `/${trimmed}`
  if (withLeadingSlash === '/') {
    return '/'
  }

  return withLeadingSlash.replace(/\/+$/, '')
}

function createProxyTable(configPath: string | undefined): Record<string, ProxyOptions> {
  const proxyEntries: Record<string, ProxyOptions> = {}
  if (!configPath) {
    return proxyEntries
  }

  const resolvedPath = path.isAbsolute(configPath)
    ? configPath
    : path.resolve(process.cwd(), configPath)

  if (!fs.existsSync(resolvedPath)) {
    console.warn(`APP_TABS_CONFIG not found at ${resolvedPath}; skipping proxy setup`)
    return proxyEntries
  }

  let parsed: RawAppConfig
  try {
    const fileContents = fs.readFileSync(resolvedPath, 'utf8')
    parsed = parse(fileContents) as RawAppConfig
  } catch (error) {
    console.warn('Failed to load APP_TABS_CONFIG, skipping proxy setup', error)
    return proxyEntries
  }

  parsed.tabs?.forEach((tab) => {
    if (!tab || !tab.iframeUrl || !tab.proxyTarget) {
      return
    }

    const basePath = normalizeBasePath(tab.iframeUrl)
    if (!basePath) {
      return
    }

    proxyEntries[basePath] = {
      target: tab.proxyTarget,
      changeOrigin: true,
      ws: true,
      rewriteWsOrigin: true,
      secure: false,
      rewrite: (incomingPath) => {
        if (!incomingPath.startsWith(basePath)) {
          return incomingPath
        }

        const boundaryChar = incomingPath.charAt(basePath.length)
        if (boundaryChar && boundaryChar !== '/' && boundaryChar !== '?') {
          return incomingPath
        }

        const stripped = incomingPath.slice(basePath.length)
        if (!stripped) {
          return '/'
        }

        return stripped.startsWith('/') ? stripped : `/${stripped}`
      },
      headers: {
        'X-Forwarded-Proto': 'http',
      },
    }
  })

  return proxyEntries
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const configPath = env.APP_TABS_CONFIG
  const proxy = createProxyTable(configPath)
  const apiProxyTarget = env.API_PROXY_TARGET

  if (!configPath) {
    console.info('[vite] APP_TABS_CONFIG not set; skipping iframe proxy setup')
  } else if (Object.keys(proxy).length === 0) {
    console.info(`[vite] no iframe proxy entries created from APP_TABS_CONFIG at ${configPath}`)
  } else {
    console.info('[vite] iframe proxy entries created from APP_TABS_CONFIG:', proxy)
  }

  if (apiProxyTarget) {
    proxy['/api'] = {
      target: apiProxyTarget,
      changeOrigin: true,
      ws: true,
      secure: false,
      headers: {
        'X-Forwarded-Proto': 'http',
      },
    }
    console.info(`[vite] /api requests proxied to ${apiProxyTarget}`)
  } else {
    console.info('[vite] API_PROXY_TARGET not set; /api requests will hit Vite directly')
  }

  return {
    plugins: [react()],
    server: {
      port: 5173,
      // If you use HTTPS locally, set https: true and run code-server with TLS or let the proxy terminate TLS.
      // https: true,
      proxy,
    },
  }
})
