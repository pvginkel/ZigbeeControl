import { useEffect } from 'react'
import AppShell from './components/AppShell'
import { useConfigQuery } from './hooks/useConfigQuery'
import { useAuth } from './hooks/useAuth'
import { useTabsStore } from './state/useTabsStore'

function App() {
  const { isChecking, isAuthenticated, authError, refetchAuth, markUnauthenticated } = useAuth()
  const { data, isLoading, isError, error, refetch } = useConfigQuery({
    enabled: isAuthenticated,
    onUnauthorized: markUnauthenticated,
  })
  const initialize = useTabsStore((state) => state.initialize)

  useEffect(() => {
    if (isAuthenticated && data) {
      initialize(data.tabs)
    }
  }, [data, initialize, isAuthenticated])

  useEffect(() => {
    if (!isChecking && !isAuthenticated && !authError) {
      window.location.href = `/api/auth/login?redirect=${encodeURIComponent(window.location.href)}`
    }
  }, [isChecking, isAuthenticated, authError])

  if (isChecking || (!isAuthenticated && !authError)) {
    return <div className="app-feedback" />
  }

  if (authError) {
    const message = authError instanceof Error ? authError.message : 'Failed to verify authentication'
    return (
      <div className="app-feedback" role="alert">
        <p>{message}</p>
        <button type="button" onClick={() => refetchAuth()}>
          Retry
        </button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="app-feedback" role="status">
        Loading configuration…
      </div>
    )
  }

  if (isError) {
    const message = error instanceof Error ? error.message : 'Failed to load configuration'
    return (
      <div className="app-feedback" role="alert">
        <p>{message}</p>
        <button type="button" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    )
  }

  if (!data || data.tabs.length === 0) {
    return (
      <div className="app-feedback" role="status">
        No tabs configured
      </div>
    )
  }

  return <AppShell tabs={data.tabs} />
}

export default App
