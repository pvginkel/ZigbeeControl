import { useEffect, useRef } from 'react'
import type { TabStatus, UiTabConfig } from '@/types/tabs'

// A rollout counts as done once the new pod is Ready, but the Service routes to it a moment later;
// until then the proxy in front of the tab answers 502. Wait for the tab's own URL to answer before
// reloading the iframe into it, and give up waiting (reloading anyway) after about 30 seconds.
const REACHABILITY_POLL_MS = 500
const REACHABILITY_MAX_ATTEMPTS = 60

async function waitUntilReachable(url: string, signal: AbortSignal): Promise<void> {
  for (let attempt = 0; attempt < REACHABILITY_MAX_ATTEMPTS; attempt++) {
    try {
      // no-cors: a cross-origin tab yields an opaque response (status 0), which counts as reachable.
      const response = await fetch(url, { method: 'HEAD', mode: 'no-cors', cache: 'no-store', signal })
      if (response.status < 500) return
    } catch {
      if (signal.aborted) return
    }
    await new Promise((resolve) => setTimeout(resolve, REACHABILITY_POLL_MS))
  }
}

interface TabContentProps {
  tab: UiTabConfig
  index: number
  isActive: boolean
  isMounted: boolean
  status: TabStatus
}

export function TabContent({ tab, index, isActive, isMounted, status }: TabContentProps) {
  const panelId = `tabpanel-${index}`
  const tabId = `tab-${index}`
  const iframeRef = useRef<HTMLIFrameElement | null>(null)
  const previousStatusRef = useRef<TabStatus | undefined>(undefined)

  useEffect(() => {
    if (!isMounted) {
      previousStatusRef.current = status
      return
    }

    const previousStatus = previousStatusRef.current
    previousStatusRef.current = status

    if (previousStatus === 'restarting' && status !== 'restarting') {
      const frame = iframeRef.current
      if (!frame) return
      const controller = new AbortController()
      void waitUntilReachable(tab.iframeUrl, controller.signal).then(() => {
        if (controller.signal.aborted) return
        try {
          frame.contentWindow?.location.reload()
        } catch {
          frame.src = tab.iframeUrl
        }
      })
      return () => controller.abort()
    }
  }, [isMounted, status, tab.iframeUrl])

  return (
    <div
      id={panelId}
      role="tabpanel"
      aria-labelledby={tabId}
      aria-hidden={!isActive}
      tabIndex={isActive ? 0 : -1}
      className={`absolute inset-0 ${isActive ? 'block' : 'hidden'}`}
      style={{ backgroundColor: tab.tabColor ?? '#080b0f' }}
      hidden={!isActive}
      data-testid={`tab.panel.${index}`}
    >
      {isMounted && (
        <iframe
          ref={iframeRef}
          title={tab.text}
          src={tab.iframeUrl}
          className="size-full border-none"
          style={{ backgroundColor: tab.tabColor ?? '#0f141b' }}
          data-testid={`tab.iframe.${index}`}
        />
      )}
    </div>
  )
}
