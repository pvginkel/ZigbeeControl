import { expect, type Locator, type Page } from '@playwright/test'
import { BasePage } from './base-page'

/**
 * Page object for the ZigbeeControl tab manager.
 * Provides helpers for interacting with tabs, iframes, and restart buttons.
 */
export class TabManagerPage extends BasePage {
  readonly manager: Locator
  readonly tablist: Locator
  readonly panels: Locator
  readonly loading: Locator
  readonly error: Locator
  readonly empty: Locator
  readonly retry: Locator

  constructor(page: Page) {
    super(page)
    this.manager = page.getByTestId('tab-manager')
    this.tablist = page.getByTestId('tab-manager.tablist')
    this.panels = page.getByTestId('tab-manager.panels')
    this.loading = page.getByTestId('tab-manager.loading')
    this.error = page.getByTestId('tab-manager.error')
    this.empty = page.getByTestId('tab-manager.empty')
    this.retry = page.getByTestId('tab-manager.retry')
  }

  tabButton(index: number): Locator {
    return this.page.getByTestId(`tab.button.${index}`)
  }

  tabWrapper(index: number): Locator {
    return this.page.getByTestId(`tab.wrapper.${index}`)
  }

  tabPanel(index: number): Locator {
    return this.page.getByTestId(`tab.panel.${index}`)
  }

  tabIframe(index: number): Locator {
    return this.page.getByTestId(`tab.iframe.${index}`)
  }

  restartButton(index: number): Locator {
    return this.page.getByTestId(`tab.restart.${index}`)
  }

  async expectTabCount(count: number): Promise<void> {
    const buttons = this.tablist.locator('[role="tab"]')
    await expect(buttons).toHaveCount(count)
  }

  async expectActiveTab(index: number): Promise<void> {
    await expect(this.tabButton(index)).toHaveAttribute('aria-selected', 'true')
    await expect(this.tabPanel(index)).not.toHaveAttribute('hidden', '')
  }

  async selectTab(index: number): Promise<void> {
    await this.tabButton(index).click()
  }

  async expectTabLabel(index: number, label: string): Promise<void> {
    await expect(this.tabButton(index)).toContainText(label)
  }

  async expectLoading(): Promise<void> {
    await expect(this.loading).toBeVisible()
  }

  async expectLoaded(): Promise<void> {
    await expect(this.manager).toBeVisible()
  }

  async expectError(): Promise<void> {
    await expect(this.error).toBeVisible()
  }

  async expectEmpty(): Promise<void> {
    await expect(this.empty).toBeVisible()
  }
}
