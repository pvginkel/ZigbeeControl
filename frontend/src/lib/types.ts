export type TabStatus = 'running' | 'restarting' | 'error'

export interface TabStatusEvent {
  tab_index: number
  state: TabStatus
  message: string | null
}

export interface K8sInfo {
  namespace: string
  deployment: string
}

export interface TabConfig {
  text: string
  iconUrl: string
  iframeUrl: string
  proxyTarget?: string
  k8s?: K8sInfo
  restartable?: boolean
  tabColor?: string
}

export interface UiTabConfig extends TabConfig {
  isRestartable: boolean
}

export interface ConfigResponse {
  tabs: TabConfig[]
}
