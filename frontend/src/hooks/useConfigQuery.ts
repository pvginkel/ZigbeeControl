import { useQuery } from '@tanstack/react-query'
import { fetchConfig, isUnauthorizedError } from '../lib/api'
import type { ConfigResponse, UiTabConfig } from '../lib/types'

interface ConfigQueryResult {
  tabs: UiTabConfig[]
}

interface UseConfigQueryOptions {
  enabled?: boolean
  onUnauthorized?: () => void
}

function normalizeConfig(response: ConfigResponse): ConfigQueryResult {
  const tabs: UiTabConfig[] = response.tabs.map((tab) => ({
    ...tab,
    isRestartable: tab.restartable ?? Boolean(tab.k8s),
  }))

  return { tabs }
}

export function useConfigQuery(options: UseConfigQueryOptions = {}) {
  const { enabled = true, onUnauthorized } = options

  return useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      try {
        return await fetchConfig()
      } catch (error) {
        if (isUnauthorizedError(error)) {
          onUnauthorized?.()
        }
        throw error
      }
    },
    select: normalizeConfig,
    staleTime: Infinity,
    gcTime: Infinity,
    enabled,
    retry: false,
  })
}
