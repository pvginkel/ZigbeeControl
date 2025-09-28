import { useQuery } from '@tanstack/react-query'
import { fetchConfig } from '../lib/api'
import type { ConfigResponse, UiTabConfig } from '../lib/types'

interface ConfigQueryResult {
  tabs: UiTabConfig[]
}

function normalizeConfig(response: ConfigResponse): ConfigQueryResult {
  const tabs: UiTabConfig[] = response.tabs.map((tab) => ({
    ...tab,
    isRestartable: tab.restartable ?? Boolean(tab.k8s),
  }))

  return { tabs }
}

export function useConfigQuery() {
  return useQuery({
    queryKey: ['config'],
    queryFn: fetchConfig,
    select: normalizeConfig,
    staleTime: Infinity,
    gcTime: Infinity,
  })
}
