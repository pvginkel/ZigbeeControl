export type TabStatus = 'running' | 'restarting' | 'error'

export interface K8sInfo {
  namespace: string
  deployment: string
}

export interface TabConfig {
  text: string
  iconUrl: string
  iframeUrl: string
  k8s?: K8sInfo
}

export interface UiTabConfig extends TabConfig {
  isRestartable: boolean
}

export interface ConfigResponse {
  tabs: TabConfig[]
}
