export type TabStatus = 'running' | 'restarting' | 'error'

export interface TabStatusEvent {
  tab_index: number
  state: TabStatus
  message: string | null
}

interface TabConfig {
  text: string
  iconUrl: string
  iframeUrl: string
  restartable?: boolean
  tabColor?: string
}

export interface UiTabConfig extends TabConfig {
  isRestartable: boolean
}