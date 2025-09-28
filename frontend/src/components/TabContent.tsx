import { useEffect, useRef } from 'react'
import type { TabStatus, UiTabConfig } from '../lib/types'

interface TabContentProps {
  tab: UiTabConfig
  index: number
  isActive: boolean
  isMounted: boolean
  status?: TabStatus
}

export default function TabContent({ tab, index, isActive, isMounted, status }: TabContentProps) {
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

    if (previousStatus === 'restarting' && status && status !== 'restarting') {
      const frame = iframeRef.current
      if (!frame) {
        return
      }

      try {
        frame.contentWindow?.location.reload()
      } catch (error) {
        console.warn('Falling back to src reset during iframe reload', error)
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
      className={`tab-panel${isActive ? ' tab-panel--active' : ''}`}
      hidden={!isActive}
    >
      {isMounted ? (
        <iframe
          ref={iframeRef}
          title={tab.text}
          src={tab.iframeUrl}
          className="tab-panel__iframe"
        />
      ) : null}
    </div>
  )
}
