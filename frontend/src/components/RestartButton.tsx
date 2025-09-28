import { useEffect, useState, type MouseEvent } from 'react'
import { useRestartMutation } from '../hooks/useRestartMutation'
import type { TabStatus } from '../lib/types'

interface RestartButtonProps {
  tabIndex: number
  status: TabStatus
  label: string
}

export default function RestartButton({ tabIndex, status, label }: RestartButtonProps) {
  const { mutate, isPending } = useRestartMutation(tabIndex)
  const [isHovering, setIsHovering] = useState(false)

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    event.preventDefault()
    mutate()
  }

  const handleHoverChange = (hovering: boolean) => {
    setIsHovering(hovering)
  }

  const disabled = status === 'restarting' || isPending

  useEffect(() => {
    if (disabled) {
      setIsHovering(false)
    }
  }, [disabled])

  const iconName = status === 'error'
    ? 'exclamation'
    : status === 'restarting' || (isHovering && !disabled)
      ? 'cached'
      : 'play_arrow'

  return (
    <button
      type="button"
      className="restart-button"
      aria-label={`Restart ${label}`}
      aria-disabled={disabled}
      onClick={handleClick}
      onMouseEnter={() => handleHoverChange(true)}
      onMouseLeave={() => handleHoverChange(false)}
      onFocus={() => handleHoverChange(true)}
      onBlur={() => handleHoverChange(false)}
      disabled={disabled}
      data-status={status}
    >
      <span className="restart-button__icon material-icon" aria-hidden="true">{iconName}</span>
    </button>
  )
}
