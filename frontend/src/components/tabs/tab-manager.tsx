import { useConfigQuery } from '@/hooks/use-config-query'
import type { UiTabConfig } from '@/types/tabs'
import { TabShell } from './tab-shell'

export function TabManager() {
  const { data: rawData, isLoading, isError, error, refetch } = useConfigQuery()
  const data = rawData as unknown as { tabs: UiTabConfig[] } | undefined
  const tabs = data?.tabs

  if (isLoading) {
    return (
      <div
        className="grid min-h-screen flex-1 place-items-center text-[rgba(236,238,242,0.82)]"
        style={{ background: 'rgba(12, 17, 23, 0.92)' }}
        role="status"
        data-testid="tab-manager.loading"
      >
        Loading configuration...
      </div>
    )
  }

  if (isError) {
    return (
      <div
        className="grid min-h-screen flex-1 place-items-center gap-4 text-center text-[rgba(236,238,242,0.82)]"
        style={{ background: 'rgba(12, 17, 23, 0.92)' }}
        role="alert"
        data-testid="tab-manager.error"
      >
        <div className="flex flex-col items-center gap-4">
          <p>{error instanceof Error ? error.message : 'Failed to load configuration'}</p>
          <button
            type="button"
            className="cursor-pointer rounded-full border border-[rgba(116,168,255,0.5)] px-[1.1rem] py-2 text-[#e7f1ff] transition-[background,border-color] duration-200 hover:bg-[rgba(82,113,162,0.6)] focus-visible:outline-2 focus-visible:outline-[#5da0ff] focus-visible:outline-offset-2"
            style={{ background: 'rgba(50, 74, 112, 0.55)' }}
            onClick={() => refetch()}
            data-testid="tab-manager.retry"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!tabs || tabs.length === 0) {
    return (
      <div
        className="grid min-h-screen flex-1 place-items-center text-[rgba(236,238,242,0.82)]"
        style={{ background: 'rgba(12, 17, 23, 0.92)' }}
        role="status"
        data-testid="tab-manager.empty"
      >
        No tabs configured
      </div>
    )
  }

  return <TabShell tabs={tabs} />
}
