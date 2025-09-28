import type { MouseEvent } from 'react'
import { useRestartMutation } from '../hooks/useRestartMutation'
import type { TabStatus } from '../lib/types'

interface RestartButtonProps {
  tabIndex: number
  status: TabStatus
  label: string
}

function RestartGlyph() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path
        d="M10 3a7 7 0 0 1 4.77 1.87l1.37-1.37V8h-4.5l1.7-1.7A4.5 4.5 0 1 0 14.5 12H16a6 6 0 1 1-6-9z"
        fill="currentColor"
      />
    </svg>
  )
}

export default function RestartButton({ tabIndex, status, label }: RestartButtonProps) {
  const { mutate, isPending } = useRestartMutation(tabIndex)

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    event.preventDefault()
    mutate()
  }

  const disabled = status === 'restarting' || isPending

  return (
    <button
      type="button"
      className="restart-button"
      aria-label={`Restart ${label}`}
      aria-disabled={disabled}
      onClick={handleClick}
      disabled={disabled}
    >
      <RestartGlyph />
    </button>
  )
}
