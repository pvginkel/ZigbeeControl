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

function RestartingIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 5a7 7 0 0 1 4.95 2.05L19 6v5h-5l1.84-1.84A5 5 0 1 0 17 14h2a7 7 0 1 1-7-9z"
        fill="currentColor"
      />
    </svg>
  )
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

  return (
    <div className={`tab-button-wrapper${isActive ? ' tab-button-wrapper--active' : ''}`} data-status={tabStatus}>
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
          {tabStatus === 'restarting' ? (
            <RestartingIcon />
          ) : (
            <img src={tab.iconUrl} alt="" />
          )}
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
