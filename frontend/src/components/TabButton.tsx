import type { CSSProperties } from 'react'
import type { TabStatus, UiTabConfig } from '../lib/types'
import RestartButton from './RestartButton'

interface TabButtonProps {
  tab: UiTabConfig
  index: number
  isActive: boolean
  status?: TabStatus
  onSelect(index: number): void
  buttonRef: (node: HTMLButtonElement | null) => void
}

export default function TabButton({
  tab,
  index,
  isActive,
  status,
  onSelect,
  buttonRef,
}: TabButtonProps) {
  const tabId = `tab-${index}`
  const panelId = `tabpanel-${index}`
  const tabStatus = status ?? 'running'
  const tabColor = tab.tabColor ?? '#1c2330'
  const wrapperStyle = { '--tab-color': tabColor } as CSSProperties

  return (
    <div
      className={`tab-button-wrapper${isActive ? ' tab-button-wrapper--active' : ''}`}
      data-status={tabStatus}
      style={wrapperStyle}
    >
      <button
        ref={buttonRef}
        id={tabId}
        type="button"
        role="tab"
        aria-selected={isActive}
        aria-controls={panelId}
        tabIndex={isActive ? 0 : -1}
        className="tab-button"
        onClick={() => onSelect(index)}
      >
        <span className="tab-button__icon" aria-hidden="true" data-status={tabStatus}>
          <img src={tab.iconUrl} alt="" />
          {tabStatus === 'error' ? <span className="tab-button__icon-badge" /> : null}
        </span>
        <span className="tab-button__label">{tab.text}</span>
      </button>
      {tab.isRestartable ? (
        <RestartButton tabIndex={index} status={tabStatus} label={tab.text} />
      ) : null}
    </div>
  )
}
