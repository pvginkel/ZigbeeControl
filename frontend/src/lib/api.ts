import type { ConfigResponse } from './types'

const API_BASE_PATH = '/api/'

export class ApiError extends Error {
  status: number
  details: unknown

  constructor(message: string, status: number, details: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message = 'Authentication required', status = 401, details: unknown = null) {
    super(message, status, details)
    this.name = 'UnauthorizedError'
  }
}

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

async function handleErrorResponse(response: Response, fallbackMessage: string): Promise<never> {
  let message = fallbackMessage
  let details: unknown = null

  const contentType = response.headers.get('content-type') ?? ''

  if (contentType.includes('application/json')) {
    details = await response
      .json()
      .catch(() => null)
    if (details && typeof details === 'object') {
      const record = details as Record<string, unknown>
      const maybeMessage = record.message ?? record.error
      if (typeof maybeMessage === 'string' && maybeMessage.trim().length > 0) {
        message = maybeMessage
      }
    }
  } else {
    const text = await response.text().catch(() => '')
    if (text.trim().length > 0) {
      message = text
    }
  }

  if (response.status === 401 || response.status === 403) {
    throw new UnauthorizedError(message, response.status, details)
  }

  throw new ApiError(message, response.status, details)
}

export async function fetchConfig(): Promise<ConfigResponse> {
  const response = await fetch(buildUrl('config'), {
    headers: JSON_HEADERS,
  })

  if (!response.ok) {
    await handleErrorResponse(response, `Config request failed with status ${response.status}`)
  }

  return parseJsonResponse<ConfigResponse>(response)
}

export async function restartTab(tabIndex: number): Promise<void> {
  const response = await fetch(buildUrl(`restart/${tabIndex}`), {
    method: 'POST',
    headers: JSON_HEADERS,
  })

  if (!response.ok) {
    await handleErrorResponse(response, `Restart failed with status ${response.status}`)
  }
}

export function openStatusStream(tabIndex: number): EventSource {
  return new EventSource(buildUrl(`status/${tabIndex}/stream`), { withCredentials: true })
}

export async function checkAuth(): Promise<void> {
  const response = await fetch(buildUrl('auth/check'), {
    headers: JSON_HEADERS,
  })

  if (!response.ok) {
    await handleErrorResponse(response, `Auth check failed with status ${response.status}`)
  }
}

export async function login(password: string): Promise<void> {
  const response = await fetch(buildUrl('auth/login'), {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ token: password }),
  })

  if (!response.ok) {
    await handleErrorResponse(response, `Login failed with status ${response.status}`)
  }
}

export function isUnauthorizedError(error: unknown): error is UnauthorizedError {
  return error instanceof UnauthorizedError
}
