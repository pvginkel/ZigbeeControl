import { create } from 'zustand'
import type { TabStatus, UiTabConfig } from '../lib/types'

type StatusMap = Record<number, TabStatus>

interface TabsState {
  activeIndex: number
  mounted: Record<number, boolean>
  statuses: StatusMap
  initialize(tabs: UiTabConfig[]): void
  setActiveIndex(index: number): void
  markMounted(index: number): void
  setStatus(index: number, status: TabStatus): void
}

export const useTabsStore = create<TabsState>((set) => ({
  activeIndex: 0,
  mounted: {},
  statuses: {},
  initialize: (tabs) => {
    set(() => {
      const initialStatuses: StatusMap = {}
      tabs.forEach((tab, index) => {
        if (tab.isRestartable) {
          initialStatuses[index] = 'running'
        }
      })

      return {
        activeIndex: 0,
        mounted: tabs.length > 0 ? { 0: true } : {},
        statuses: initialStatuses,
      }
    })
  },
  setActiveIndex: (index) => {
    set((state) => {
      const alreadyMounted = state.mounted[index]
      return {
        activeIndex: index,
        mounted: alreadyMounted
          ? state.mounted
          : { ...state.mounted, [index]: true },
      }
    })
  },
  markMounted: (index) => {
    set((state) => {
      if (state.mounted[index]) {
        return state
      }

      return {
        ...state,
        mounted: { ...state.mounted, [index]: true },
      }
    })
  },
  setStatus: (index, status) => {
    set((state) => {
      if (state.statuses[index] === status) {
        return state
      }

      return {
        statuses: { ...state.statuses, [index]: status },
      }
    })
  },
}))
