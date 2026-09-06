import { useCallback, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { UserDropdown } from '@/components/layout/user-dropdown'
import { useTabStatusSse } from '@/hooks/use-tab-status-sse'
import type { TabStatus, UiTabConfig } from '@/types/tabs'
import { TabButton } from './tab-button'
import { TabContent } from './tab-content'

interface TabShellProps {
  tabs: UiTabConfig[]
}

function buildInitialStatuses(tabs: UiTabConfig[]): Record<number, TabStatus> {
  const statuses: Record<number, TabStatus> = {}
  tabs.forEach((tab, i) => {
    if (tab.isRestartable) statuses[i] = 'running'
  })
  return statuses
}

export function TabShell({ tabs }: TabShellProps) {
  const [activeIndex, setActiveIndex] = useState(0)
  const [mounted, setMounted] = useState<Record<number, boolean>>({ 0: true })
  const [statuses, setStatuses] = useState<Record<number, TabStatus>>(() => buildInitialStatuses(tabs))
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([])

  const handleStatusChange = useCallback((index: number, status: TabStatus) => {
    setStatuses((prev) => {
      if (prev[index] === status) return prev
      return { ...prev, [index]: status }
    })
  }, [])

  const getStatus = useCallback((index: number): TabStatus => {
    return statuses[index] ?? 'running'
  }, [statuses])

  // SSE tab status updates via template's SSE context
  useTabStatusSse(handleStatusChange)

  const handleSelect = useCallback((index: number) => {
    setActiveIndex(index)
    setMounted((prev) => prev[index] ? prev : { ...prev, [index]: true })
  }, [])

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (tabs.length === 0) return

      let nextIndex = activeIndex
      if (event.key === 'ArrowRight') {
        nextIndex = (activeIndex + 1) % tabs.length
      } else if (event.key === 'ArrowLeft') {
        nextIndex = (activeIndex - 1 + tabs.length) % tabs.length
      } else if (event.key === 'Home') {
        nextIndex = 0
      } else if (event.key === 'End') {
        nextIndex = tabs.length - 1
      } else {
        return
      }

      event.preventDefault()
      tabRefs.current[nextIndex]?.focus()
      handleSelect(nextIndex)
    },
    [activeIndex, tabs.length, handleSelect],
  )

  return (
    <div
      className="flex flex-1 flex-col overflow-hidden"
      style={{ background: 'linear-gradient(180deg, rgba(20, 26, 34, 0.92) 0%, rgba(15, 20, 27, 0.98) 100%)' }}
      data-testid="tab-manager"
    >
      {/* Tab bar */}
      <div className="sticky top-0 z-10 flex items-center gap-[0.3rem] bg-[#0d1218] px-3 pt-[3px] max-md:flex-wrap max-md:gap-2">
        <div
          className="flex items-stretch gap-[0.3rem] max-md:flex-wrap max-md:gap-2"
          role="tablist"
          aria-label="Application tabs"
          aria-orientation="horizontal"
          onKeyDown={handleKeyDown}
          data-testid="tab-manager.tablist"
        >
          {tabs.map((tab, index) => (
            <TabButton
              key={`${tab.text}-${index}`}
              tab={tab}
              index={index}
              isActive={index === activeIndex}
              status={statuses[index] ?? 'running'}
              onSelect={handleSelect}
              onStatusChange={handleStatusChange}
              getStatus={getStatus}
              buttonRef={(node) => { tabRefs.current[index] = node }}
            />
          ))}
        </div>
        <div className="flex-1" />
        <UserDropdown />
      </div>
      {/* Tab panels */}
      <div
        className="relative flex-1 overflow-hidden transition-colors duration-200"
        style={{ backgroundColor: tabs[activeIndex]?.tabColor ?? '#080b0f' }}
        data-testid="tab-manager.panels"
      >
        {tabs.map((tab, index) => (
          <TabContent
            key={`${tab.text}-${index}`}
            tab={tab}
            index={index}
            isActive={index === activeIndex}
            isMounted={Boolean(mounted[index])}
            status={statuses[index] ?? 'running'}
          />
        ))}
      </div>
    </div>
  )
}
