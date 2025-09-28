import type { UiTabConfig } from '../lib/types'

interface TabContentProps {
  tab: UiTabConfig
  index: number
  isActive: boolean
  isMounted: boolean
}

export default function TabContent({ tab, index, isActive, isMounted }: TabContentProps) {
  const panelId = `tabpanel-${index}`
  const tabId = `tab-${index}`

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
          title={tab.text}
          src={tab.iframeUrl}
          className="tab-panel__iframe"
          allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          sandbox="allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-presentation allow-same-origin allow-scripts"
        />
      ) : null}
    </div>
  )
}
