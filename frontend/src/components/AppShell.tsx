import { useCallback, useEffect, useRef } from 'react'
import type { KeyboardEvent } from 'react'
import type { UiTabConfig } from '../lib/types'
import { useTabsStore } from '../state/useTabsStore'
import TabButton from './TabButton'
import TabContent from './TabContent'
import { useSseStatus } from '../hooks/useSseStatus'

interface AppShellProps {
  tabs: UiTabConfig[]
}

function StatusStream({ tabIndex, enabled }: { tabIndex: number; enabled: boolean }) {
  useSseStatus(tabIndex, enabled)
  return null
}

export default function AppShell({ tabs }: AppShellProps) {
  const activeIndex = useTabsStore((state) => state.activeIndex)
  const setActiveIndex = useTabsStore((state) => state.setActiveIndex)
  const mounted = useTabsStore((state) => state.mounted)
  const statuses = useTabsStore((state) => state.statuses)
  const markMounted = useTabsStore((state) => state.markMounted)
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([])

  useEffect(() => {
    if (tabs.length > 0) {
      markMounted(activeIndex)
    }
  }, [activeIndex, markMounted, tabs.length])

  const focusTab = useCallback((index: number) => {
    tabRefs.current[index]?.focus()
  }, [])

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (tabs.length === 0) {
        return
      }

      const key = event.key
      let nextIndex = activeIndex

      if (key === 'ArrowRight') {
        nextIndex = (activeIndex + 1) % tabs.length
      } else if (key === 'ArrowLeft') {
        nextIndex = (activeIndex - 1 + tabs.length) % tabs.length
      } else if (key === 'Home') {
        nextIndex = 0
      } else if (key === 'End') {
        nextIndex = tabs.length - 1
      } else {
        return
      }

      event.preventDefault()
      focusTab(nextIndex)
      setActiveIndex(nextIndex)
    },
    [activeIndex, focusTab, setActiveIndex, tabs.length],
  )

  const handleSelect = useCallback(
    (index: number) => {
      setActiveIndex(index)
    },
    [setActiveIndex],
  )

  return (
    <div className="app-shell">
      <div
        className="tablist"
        role="tablist"
        aria-label="Zigbee wrapper tabs"
        aria-orientation="horizontal"
        onKeyDown={handleKeyDown}
      >
        {tabs.map((tab, index) => (
          <TabButton
            key={`${tab.text}-${index}`}
            tab={tab}
            index={index}
            isActive={index === activeIndex}
            status={statuses[index]}
            onSelect={handleSelect}
            buttonRef={(node) => {
              tabRefs.current[index] = node
            }}
          />
        ))}
      </div>
      <div className="tabpanels">
        {tabs.map((tab, index) => (
          <TabContent
            key={`${tab.text}-${index}`}
            tab={tab}
            index={index}
            isActive={index === activeIndex}
            isMounted={Boolean(mounted[index])}
            status={statuses[index]}
          />
        ))}
      </div>
      {tabs.map((tab, index) => (
        <StatusStream key={`status-${index}`} tabIndex={index} enabled={tab.isRestartable} />
      ))}
    </div>
  )
}
