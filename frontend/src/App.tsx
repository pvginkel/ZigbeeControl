import { useEffect } from 'react'
import AppShell from './components/AppShell'
import { useConfigQuery } from './hooks/useConfigQuery'
import { useTabsStore } from './state/useTabsStore'

function App() {
  const { data, isLoading, isError, error, refetch } = useConfigQuery()
  const initialize = useTabsStore((state) => state.initialize)

  useEffect(() => {
    if (data) {
      initialize(data.tabs)
    }
  }, [data, initialize])

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
