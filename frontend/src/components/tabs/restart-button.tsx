import { useState } from 'react'
import type { MouseEvent } from 'react'
import { useRestartMutation } from '@/hooks/use-restart-mutation'
import type { TabStatus } from '@/types/tabs'

interface RestartButtonProps {
  tabIndex: number
  status: TabStatus
  label: string
  onStatusChange: (index: number, status: TabStatus) => void
  getStatus: (index: number) => TabStatus
}

export function RestartButton({ tabIndex, status, label, onStatusChange, getStatus }: RestartButtonProps) {
  const { mutate, isPending } = useRestartMutation({ tabIndex, onStatusChange, getStatus })
  const [isHovering, setIsHovering] = useState(false)

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    event.preventDefault()
    mutate({ path: { idx: tabIndex } })
  }

  const disabled = status === 'restarting' || isPending
  const effectiveHover = isHovering && !disabled

  // Material Symbols icon names — matching original exactly
  const iconName = status === 'error'
    ? 'exclamation'
    : status === 'restarting' || effectiveHover
      ? 'cached'
      : 'play_arrow'

  const bg = status === 'error'
    ? '#ff7e7e'
    : '#545454'

  return (
    <button
      type="button"
      className="mr-2 inline-flex size-[1.3rem] flex-none items-center justify-center rounded-full border-none p-0 text-white transition-[background,opacity] duration-150 focus-visible:outline-2 focus-visible:outline-[#4a90ff] focus-visible:outline-offset-2"
      style={{
        backgroundColor: bg,
        opacity: disabled ? 0.45 : undefined,
        cursor: disabled ? 'default' : 'pointer',
      }}
      aria-label={`Restart ${label}`}
      aria-disabled={disabled}
      onClick={handleClick}
      onMouseEnter={(e) => {
        setIsHovering(true)
        if (!disabled && status !== 'error') e.currentTarget.style.backgroundColor = '#5f5f5f'
      }}
      onMouseLeave={(e) => {
        setIsHovering(false)
        e.currentTarget.style.backgroundColor = bg
      }}
      onMouseDown={(e) => {
        if (!disabled && status !== 'error') e.currentTarget.style.backgroundColor = '#8f8f8f'
      }}
      onMouseUp={(e) => {
        if (!disabled && status !== 'error') e.currentTarget.style.backgroundColor = '#5f5f5f'
      }}
      onFocus={() => setIsHovering(true)}
      onBlur={() => setIsHovering(false)}
      disabled={disabled}
      data-status={status}
      data-testid={`tab.restart.${tabIndex}`}
    >
      <span
        className="material-icon text-[0.9rem]"
        aria-hidden="true"
        style={status === 'restarting' ? { animation: 'restartBlink 0.9s steps(1, end) infinite' } : undefined}
      >
        {iconName}
      </span>
    </button>
  )
}
