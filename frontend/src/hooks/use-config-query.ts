import { useGetConfig, type ConfigResponse_6be28b6 } from '@/lib/api/generated/hooks'
import type { UiTabConfig } from '@/types/tabs'

interface ConfigQueryResult {
  tabs: UiTabConfig[]
}

function normalizeConfig(data: ConfigResponse_6be28b6): ConfigQueryResult {
  const tabs: UiTabConfig[] = (data.tabs ?? []).map((tab) => ({
    text: tab.text,
    iconUrl: tab.iconUrl,
    iframeUrl: tab.iframeUrl,
    restartable: tab.restartable,
    tabColor: tab.tabColor ?? undefined,
    isRestartable: tab.restartable,
  }))
  return { tabs }
}

export function useConfigQuery() {
  return useGetConfig(undefined, {
    select: normalizeConfig as (data: unknown) => unknown,
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
  })
}
