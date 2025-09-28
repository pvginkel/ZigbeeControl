import { useEffect, useRef } from 'react'
import { openStatusStream } from '../lib/api'
import type { TabStatus } from '../lib/types'
import { useTabsStore } from '../state/useTabsStore'

const BACKOFF_BASE_MS = 3000
const BACKOFF_MULTIPLIER = 2
const BACKOFF_MAX_MS = 30000

type StatusPayload = {
  status?: TabStatus
  state?: TabStatus
}

function parseStatus(data: string): TabStatus | null {
  try {
    const payload = JSON.parse(data) as StatusPayload
    const status = payload.status ?? payload.state
    if (status === 'running' || status === 'restarting' || status === 'error') {
      return status
    }
  } catch (error) {
    console.warn('Failed to parse SSE status payload', error)
  }
  return null
}

export function useSseStatus(tabIndex: number, enabled: boolean) {
  const setStatus = useTabsStore((state) => state.setStatus)
  const retryAttemptRef = useRef(0)
  const timeoutRef = useRef<number | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!enabled) {
      return
    }

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

    const handleStatus = (payload: string) => {
      const parsed = parseStatus(payload)
      if (parsed) {
        setStatus(tabIndex, parsed)
      }
    }

    const connect = () => {
      if (isDisposed) {
        return
      }

      disconnect()

      try {
        const source = openStatusStream(tabIndex)
        eventSourceRef.current = source

        source.addEventListener('open', () => {
          retryAttemptRef.current = 0
        })

        source.addEventListener('status', (event) => {
          const messageEvent = event as MessageEvent<string>
          handleStatus(messageEvent.data)
        })

        source.onmessage = (event) => {
          handleStatus(event.data)
        }

        source.onerror = () => {
          disconnect()
          scheduleReconnect()
        }
      } catch (error) {
        console.warn(`Failed to open SSE stream for tab ${tabIndex}`, error)
        scheduleReconnect()
      }
    }

    connect()

    return () => {
      isDisposed = true
      clearTimer()
      disconnect()
    }
  }, [enabled, setStatus, tabIndex])
}
