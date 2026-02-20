import { useEffect } from 'react'
import { useSseContext } from '@/contexts/sse-context'
import type { TabStatus, TabStatusEvent } from '@/types/tabs'

function isTabStatusEvent(data: unknown): data is TabStatusEvent {
  if (typeof data !== 'object' || data === null) return false
  const obj = data as Record<string, unknown>
  return (
    typeof obj.tab_index === 'number' &&
    (obj.state === 'running' || obj.state === 'restarting' || obj.state === 'error')
  )
}

/**
 * Subscribe to tab_status SSE events and forward them to a callback.
 * Uses the template's SSE context for connection management.
 */
export function useTabStatusSse(onStatusChange: (index: number, status: TabStatus) => void) {
  const { addEventListener } = useSseContext()

  useEffect(() => {
    const unsubscribe = addEventListener('tab_status', (data: unknown) => {
      if (isTabStatusEvent(data)) {
        onStatusChange(data.tab_index, data.state)
      }
    })
    return unsubscribe
  }, [addEventListener, onStatusChange])
}
