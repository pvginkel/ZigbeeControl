import type { ProxyOptions } from 'vite'
import 'dotenv/config'
import fs from 'fs'
import path from 'path'
import YAML from 'yaml'

/**
 * Read APP_TABS_CONFIG YAML and create Vite proxies for each tab's iframe.
 * In production, nginx handles the proxying; this is only for development.
 */
export function loadAppProxies(): Record<string, ProxyOptions> {
  const configPath = process.env.APP_TABS_CONFIG
  console.warn(`[vite] ${process.env.APP_TABS_CONFIG}`)
  if (!configPath) return {}

  const resolvedPath = path.isAbsolute(configPath)
    ? configPath
    : path.resolve(process.cwd(), configPath)

  if (!fs.existsSync(resolvedPath)) {
    console.warn(`[vite] APP_TABS_CONFIG not found: ${resolvedPath}`)
    return {}
  }

  try {
    const content = fs.readFileSync(resolvedPath, 'utf8')
    const config = YAML.parse(content) as { tabs?: Array<{ iframeUrl?: string; proxyTarget?: string }> }
    const proxies: Record<string, ProxyOptions> = {}

    for (const tab of config.tabs ?? []) {
      if (tab.iframeUrl && tab.proxyTarget) {
        const basePath = tab.iframeUrl.replace(/\/+$/, '')
        if (!basePath) continue

        proxies[basePath] = {
          target: tab.proxyTarget,
          changeOrigin: true,
          ws: true,
          rewriteWsOrigin: true,
          secure: false,
          rewrite: (reqPath: string) => {
            if (!reqPath.startsWith(basePath)) return reqPath

            const boundaryChar = reqPath.charAt(basePath.length)
            if (boundaryChar && boundaryChar !== '/' && boundaryChar !== '?') return reqPath

            const stripped = reqPath.slice(basePath.length)
            if (!stripped) return '/'
            return stripped.startsWith('/') ? stripped : `/${stripped}`
          },
          headers: { 'X-Forwarded-Proto': 'http' },
        }
        console.log(`[vite] Iframe proxy: ${basePath} → ${tab.proxyTarget}`)
      }
    }

    return proxies
  } catch (error) {
    console.warn('[vite] Failed to parse APP_TABS_CONFIG:', error)
    return {}
  }
}
