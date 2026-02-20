/**
 * Domain-specific test fixtures for ZigbeeControl.
 * Extends infrastructure fixtures with the TabManagerPage page object.
 */

/* eslint-disable react-hooks/rules-of-hooks */
import { infrastructureFixtures } from './fixtures-infrastructure'
import type { InfrastructureFixtures } from './fixtures-infrastructure'
import { TabManagerPage } from './page-objects/tab-manager-page'

export interface DomainFixtures extends InfrastructureFixtures {
  tabManager: TabManagerPage
}

export const test = infrastructureFixtures.extend<Pick<DomainFixtures, 'tabManager'>>({
  tabManager: async ({ page }, use) => {
    await use(new TabManagerPage(page))
  },
})

export { expect } from '@playwright/test'
