import { useMutation } from '@tanstack/react-query'
import { restartTab, isUnauthorizedError } from '../lib/api'
import type { TabStatus } from '../lib/types'
import { useTabsStore } from '../state/useTabsStore'
import { useAuthActions } from './useAuth'

interface MutationContext {
  previousStatus: TabStatus
}

export function useRestartMutation(tabIndex: number) {
  const setStatus = useTabsStore((state) => state.setStatus)
  const { markUnauthenticated } = useAuthActions()

  return useMutation<void, Error, void, MutationContext>({
    mutationKey: ['restart', tabIndex],
    mutationFn: () => restartTab(tabIndex),
    onMutate: async () => {
      const { statuses } = useTabsStore.getState()
      const previousStatus: TabStatus = statuses[tabIndex] ?? 'running'
      setStatus(tabIndex, 'restarting')
      return { previousStatus }
    },
    onError: (error, _variables, context) => {
      if (context?.previousStatus) {
        setStatus(tabIndex, context.previousStatus)
      }

      if (isUnauthorizedError(error)) {
        markUnauthenticated()
        return
      }

      console.warn(`Restart failed for tab ${tabIndex}`, error)
    },
  })
}
