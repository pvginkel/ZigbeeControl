import { useEffect, useRef } from 'react'
import type { TabStatus, UiTabConfig } from '@/types/tabs'

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
      try {
        frame.contentWindow?.location.reload()
      } catch {
        frame.src = tab.iframeUrl
      }
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
