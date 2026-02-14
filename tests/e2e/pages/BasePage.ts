import { Page, Locator, expect } from '@playwright/test';

/**
 * Base Page Object with common functionality for all pages.
 */
export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to a path relative to baseURL.
   */
  async navigateTo(path: string): Promise<void> {
    await this.page.goto(path);
  }

  /**
   * Wait for page to be fully loaded (network idle).
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for an element to be visible.
   */
  async waitForElement(selector: string): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'visible' });
  }

  /**
   * Check if a toast/notification message is visible.
   */
  async expectToastMessage(text: string): Promise<void> {
    const toast = this.page.locator('.toast, [role="alert"], .notification').filter({ hasText: text });
    await expect(toast).toBeVisible({ timeout: 5000 });
  }

  /**
   * Check if a modal is currently visible.
   */
  async isModalVisible(): Promise<boolean> {
    const modal = this.page.locator('[role="dialog"], [data-testid*="modal"]');
    return modal.isVisible();
  }

  /**
   * Close modal by pressing Escape.
   */
  async closeModal(): Promise<void> {
    await this.page.keyboard.press('Escape');
  }

  /**
   * Click a button by its data-testid.
   */
  async clickButton(testId: string): Promise<void> {
    await this.page.click(`[data-testid="${testId}"]`);
  }

  /**
   * Fill an input by its data-testid.
   */
  async fillInput(testId: string, value: string): Promise<void> {
    await this.page.fill(`[data-testid="${testId}"]`, value);
  }

  /**
   * Get text content of an element by data-testid.
   */
  async getTextContent(testId: string): Promise<string> {
    const element = this.page.locator(`[data-testid="${testId}"]`);
    return (await element.textContent()) || '';
  }

  /**
   * Wait for loading to complete (spinner to disappear).
   */
  async waitForLoadingComplete(): Promise<void> {
    const spinner = this.page.locator('.spinner, .loading, [data-loading="true"]');
    await spinner.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {
      // Spinner might not exist, that's fine
    });
  }

  /**
   * Confirm a dialog by clicking the confirm button.
   */
  async confirmDialog(): Promise<void> {
    // Try common confirm button patterns
    const confirmBtn = this.page.locator('button:has-text("Potwierdź"), button:has-text("Tak"), button:has-text("OK"), [data-testid*="confirm"]').first();
    await confirmBtn.click();
  }
}
