import { usePostRestartByIdx } from '@/lib/api/generated/hooks'
import { useToast } from './use-toast'
import type { TabStatus } from '@/types/tabs'

interface UseRestartMutationOptions {
  tabIndex: number
  onStatusChange: (index: number, status: TabStatus) => void
  getStatus: (index: number) => TabStatus
}

export function useRestartMutation({ tabIndex, onStatusChange, getStatus }: UseRestartMutationOptions) {
  const { showException } = useToast()

  return usePostRestartByIdx({
    onMutate: (() => {
      const previousStatus = getStatus(tabIndex)
      onStatusChange(tabIndex, 'restarting')
      return { previousStatus }
    }) as () => unknown,
    onError: ((error: unknown, _variables: unknown, context: { previousStatus?: TabStatus } | undefined) => {
      if (context?.previousStatus) {
        onStatusChange(tabIndex, context.previousStatus)
      }
      showException('Restart failed', error)
    }) as (...args: unknown[]) => unknown,
  })
}
