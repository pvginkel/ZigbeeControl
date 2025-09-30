import { useCallback, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import AppShell from './components/AppShell'
import LoginScreen from './components/LoginScreen'
import { useConfigQuery } from './hooks/useConfigQuery'
import { useAuth } from './hooks/useAuth'
import { useTabsStore } from './state/useTabsStore'

function App() {
  const queryClient = useQueryClient()
  const { isChecking, isAuthenticated, authError, refetchAuth, loginMutation, markUnauthenticated } = useAuth()
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

  const handleLogin = useCallback(
    async (password: string) => {
      loginMutation.reset()
      await loginMutation.mutateAsync(password)
      await refetchAuth()
      await queryClient.invalidateQueries({ queryKey: ['config'] })
    },
    [loginMutation, queryClient, refetchAuth],
  )

  if (isChecking) {
    return (
      <div className="app-feedback" role="status">
        Checking authentication…
      </div>
    )
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

  if (!isAuthenticated) {
    const loginError = loginMutation.error instanceof Error ? loginMutation.error.message : undefined
    return <LoginScreen isSubmitting={loginMutation.isPending} onSubmit={handleLogin} errorMessage={loginError} />
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
