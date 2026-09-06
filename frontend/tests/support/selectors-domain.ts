/**
 * Domain-specific test selectors for ZigbeeControl.
 */

import { testId } from './test-id'

export const tabSelectors = {
  manager: testId('tab-manager'),
  loading: testId('tab-manager.loading'),
  error: testId('tab-manager.error'),
  empty: testId('tab-manager.empty'),
  retry: testId('tab-manager.retry'),
  tablist: testId('tab-manager.tablist'),
  panels: testId('tab-manager.panels'),
  tab: {
    wrapper: (index: number) => testId(`tab.wrapper.${index}`),
    button: (index: number) => testId(`tab.button.${index}`),
    panel: (index: number) => testId(`tab.panel.${index}`),
    iframe: (index: number) => testId(`tab.iframe.${index}`),
    restart: (index: number) => testId(`tab.restart.${index}`),
  },
}
