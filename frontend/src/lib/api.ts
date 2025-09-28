import type { ConfigResponse } from './types'

const API_BASE_PATH = '/api/'

function buildUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path
  return `${API_BASE_PATH}${normalizedPath}`
}

const JSON_HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
} as const

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const text = await response.text()
  if (!text) {
    return {} as T
  }

  try {
    return JSON.parse(text) as T
  } catch (error) {
    console.warn('Failed to parse JSON response', error)
    throw new Error('Received invalid JSON from server')
  }
}

export async function fetchConfig(): Promise<ConfigResponse> {
  const response = await fetch(buildUrl('config'), {
    headers: JSON_HEADERS,
  })

  if (!response.ok) {
    throw new Error(`Config request failed with status ${response.status}`)
  }

  return parseJsonResponse<ConfigResponse>(response)
}

export async function restartTab(tabIndex: number): Promise<void> {
  const response = await fetch(buildUrl(`restart/${tabIndex}`), {
    method: 'POST',
    headers: JSON_HEADERS,
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const message = payload?.message ?? `Restart failed with status ${response.status}`
    throw new Error(message)
  }
}

export function openStatusStream(tabIndex: number): EventSource {
  return new EventSource(buildUrl(`status/${tabIndex}/stream`), { withCredentials: false })
}
