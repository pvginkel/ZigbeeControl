import { useEffect, useRef, useState, type FormEvent } from 'react'
import '../styles/login.css'

interface LoginScreenProps {
  onSubmit: (password: string) => Promise<void>
  isSubmitting: boolean
  errorMessage?: string
}

export default function LoginScreen({ onSubmit, isSubmitting, errorMessage }: LoginScreenProps) {
  const [password, setPassword] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!password.trim()) {
      setValidationError('Password is required')
      inputRef.current?.focus()
      return
    }

    setValidationError(null)

    try {
      await onSubmit(password)
      setPassword('')
    } catch (error) {
      if (error instanceof Error && !errorMessage) {
        setValidationError(error.message)
      }
      inputRef.current?.focus()
    }
  }

  const combinedError = validationError ?? errorMessage ?? null

  return (
    <div className="login-screen">
      <form className="login-form" onSubmit={handleSubmit}>
        <div className="login-form__header">
          <h1>Enter Password</h1>
          <p>Access to the Zigbee wrapper requires the shared password.</p>
        </div>
        <div className="login-form__field">
          <label htmlFor="login-password">Password</label>
          <input
            ref={inputRef}
            id="login-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            disabled={isSubmitting}
            aria-describedby={combinedError ? 'login-error-message' : undefined}
          />
        </div>
        <div className="login-form__actions">
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </div>
        <div id="login-error-message" className="login-form__error" aria-live="polite">
          {combinedError}
        </div>
      </form>
    </div>
  )
}
