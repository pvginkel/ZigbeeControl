import { useEffect, useRef } from 'react'
import { buildSseGatewayUrl } from '../lib/api'
import type { TabStatusEvent } from '../lib/types'
import { useTabsStore } from '../state/useTabsStore'

function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  // Fallback for insecure contexts (HTTP dev)
  const bytes = new Uint8Array(16)
  crypto.getRandomValues(bytes)
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

const BACKOFF_BASE_MS = 3000
const BACKOFF_MULTIPLIER = 2
const BACKOFF_MAX_MS = 30000

function parseTabStatusEvent(data: string): TabStatusEvent | null {
  try {
    const payload = JSON.parse(data) as TabStatusEvent
    if (
      typeof payload.tab_index === 'number' &&
      (payload.state === 'running' || payload.state === 'restarting' || payload.state === 'error')
    ) {
      return payload
    }
  } catch (error) {
    console.warn('Failed to parse SSE tab_status payload', error)
  }
  return null
}

export function useSseGateway() {
  const setStatus = useTabsStore((state) => state.setStatus)
  const retryAttemptRef = useRef(0)
  const timeoutRef = useRef<number | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    let isDisposed = false

    const clearTimer = () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }

    const disconnect = () => {
      eventSourceRef.current?.close()
      eventSourceRef.current = null
    }

    const scheduleReconnect = () => {
      if (isDisposed) {
        return
      }

      const attempt = retryAttemptRef.current
      const delay = Math.min(BACKOFF_BASE_MS * BACKOFF_MULTIPLIER ** attempt, BACKOFF_MAX_MS)

      clearTimer()
      timeoutRef.current = window.setTimeout(() => {
        retryAttemptRef.current = attempt + 1
        connect()
      }, delay)
    }

    const connect = () => {
      if (isDisposed) {
        return
      }

      disconnect()

      try {
        const requestId = generateRequestId()
        const url = buildSseGatewayUrl(requestId)
        const source = new EventSource(url, { withCredentials: true })
        eventSourceRef.current = source

        source.addEventListener('open', () => {
          retryAttemptRef.current = 0
        })

        source.addEventListener('tab_status', (event) => {
          const messageEvent = event as MessageEvent<string>
          const parsed = parseTabStatusEvent(messageEvent.data)
          if (parsed) {
            setStatus(parsed.tab_index, parsed.state)
            if (parsed.message) {
              console.log(`[tab ${parsed.tab_index}] ${parsed.message}`)
            }
          }
        })

        source.onerror = () => {
          disconnect()
          scheduleReconnect()
        }
      } catch (error) {
        console.warn('Failed to open SSE Gateway stream', error)
        scheduleReconnect()
      }
    }

    connect()

    return () => {
      isDisposed = true
      clearTimer()
      disconnect()
    }
  }, [setStatus])
}
