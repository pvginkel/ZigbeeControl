import type { TabStatus, UiTabConfig } from '@/types/tabs'
import { RestartButton } from './restart-button'

interface TabButtonProps {
  tab: UiTabConfig
  index: number
  isActive: boolean
  status: TabStatus
  onSelect: (index: number) => void
  buttonRef: (node: HTMLButtonElement | null) => void
  onStatusChange: (index: number, status: TabStatus) => void
  getStatus: (index: number) => TabStatus
}

export function TabButton({
  tab,
  index,
  isActive,
  status,
  onSelect,
  buttonRef,
  onStatusChange,
  getStatus,
}: TabButtonProps) {
  const tabId = `tab-${index}`
  const panelId = `tabpanel-${index}`

  // Match original CSS color rules exactly
  const wrapperBg = status === 'error'
    ? '#261118'
    : isActive || status === 'restarting'
      ? (tab.tabColor ?? '#1c2330')
      : '#141922'

  const wrapperColor = status === 'error'
    ? '#ffb0bd'
    : isActive
      ? '#f7f8fc'
      : status === 'restarting'
        ? '#d7e4ff'
        : '#cbd0dd'

  const hoverBg = status === 'error'
    ? '#301720'
    : (tab.tabColor ?? '#191f2a')

  const hoverColor = status === 'error'
    ? '#ffd8df'
    : '#e4e8f1'

  const toplineColor = status === 'error' ? '#ff5c73' : '#3577f6'

  return (
    <div
      className="group relative inline-flex min-h-[2.25rem] items-center gap-[0.3rem] rounded-t-[2px] px-[0.4rem] transition-[background,color,opacity] duration-200"
      style={{
        backgroundColor: wrapperBg,
        color: wrapperColor,
        ['--hover-bg' as string]: hoverBg,
        ['--hover-color' as string]: hoverColor,
      }}
      data-status={status}
      data-testid={`tab.wrapper.${index}`}
      onMouseEnter={(e) => {
        if (!isActive && status !== 'restarting') {
          e.currentTarget.style.backgroundColor = hoverBg
          e.currentTarget.style.color = hoverColor
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = wrapperBg
        e.currentTarget.style.color = wrapperColor
      }}
    >
      {/* Active tab top accent line — 3px gradient matching original */}
      {(isActive || status === 'error') && (
        <div
          className="absolute inset-x-0 -top-px h-[3px] rounded-t-[6px]"
          style={{
            background: `linear-gradient(to bottom, #0d1218 0, #0d1218 1px, ${toplineColor} 1px, ${toplineColor} 100%)`,
            opacity: isActive || status === 'error' ? 1 : 0,
          }}
        />
      )}
      <button
        ref={buttonRef}
        id={tabId}
        type="button"
        role="tab"
        aria-selected={isActive}
        aria-controls={panelId}
        tabIndex={isActive ? 0 : -1}
        className="inline-flex h-full items-center gap-[0.35rem] border-none bg-transparent px-2 text-[0.875rem] font-medium text-inherit cursor-pointer focus-visible:outline-2 focus-visible:outline-[#4a90ff] focus-visible:outline-offset-2 focus-visible:rounded"
        onClick={() => onSelect(index)}
        data-testid={`tab.button.${index}`}
      >
        <span className="relative flex size-[1.1rem] items-center justify-center" aria-hidden="true" data-status={status}>
          <img src={tab.iconUrl} alt="" className="size-full" />
          {status === 'error' && (
            <span className="absolute -bottom-[0.05rem] -right-[0.05rem] size-[0.55rem] rounded-full bg-gradient-to-br from-[#ff4d4d] to-[#ffb199] border border-[rgba(12,17,23,0.92)]" />
          )}
        </span>
        <span className="whitespace-nowrap text-[0.85rem] tracking-[0.01em]">{tab.text}</span>
      </button>
      {tab.isRestartable && (
        <RestartButton
          tabIndex={index}
          status={status}
          label={tab.text}
          onStatusChange={onStatusChange}
          getStatus={getStatus}
        />
      )}
    </div>
  )
}
