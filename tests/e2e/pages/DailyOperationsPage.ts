import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Daily Operations page (/operacje).
 * Handles day open/close operations and recent days listing.
 */
export class DailyOperationsPage extends BasePage {
  // Main action buttons
  readonly openDayBtn: Locator;
  readonly closeDayBtn: Locator;
  readonly manageDayBtn: Locator;

  // Day status elements
  readonly dayStatusBadge: Locator;
  readonly currentDayCard: Locator;

  // Recent days table
  readonly recentDaysTable: Locator;
  readonly recentDaysTableBody: Locator;

  // Loading/error states
  readonly loadingSpinner: Locator;
  readonly errorAlert: Locator;

  constructor(page: Page) {
    super(page);

    // Main action buttons
    this.openDayBtn = page.locator('[data-testid="open-day-btn"]');
    this.closeDayBtn = page.locator('[data-testid="close-day-btn"]');
    this.manageDayBtn = page.locator('[data-testid="manage-day-btn"]');

    // Day status elements
    this.dayStatusBadge = page.locator('[data-testid="day-status-badge"]');
    this.currentDayCard = page.locator('[data-testid="current-day-card"]');

    // Recent days table
    this.recentDaysTable = page.locator('[data-testid="recent-days-table"]');
    this.recentDaysTableBody = this.recentDaysTable.locator('tbody');

    // Loading/error states
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"]');
    this.errorAlert = page.locator('[data-testid="error-alert"]');
  }

  /**
   * Navigate to the Daily Operations page.
   */
  async goto(): Promise<void> {
    await this.navigateTo('/operacje');
    await this.waitForPageLoad();
  }

  /**
   * Start the close day wizard by clicking the close day button.
   */
  async startCloseDay(): Promise<void> {
    await this.closeDayBtn.click();
    // Wait for wizard modal to appear
    await this.page.waitForSelector('[data-testid="close-day-wizard"]', { state: 'visible' });
  }

  /**
   * Open a new day.
   */
  async openNewDay(): Promise<void> {
    await this.openDayBtn.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Get the current day status text.
   */
  async getDayStatus(): Promise<string> {
    return (await this.dayStatusBadge.textContent()) || '';
  }

  /**
   * Check if the day is currently open.
   */
  async isDayOpen(): Promise<boolean> {
    const status = await this.getDayStatus();
    return status.toLowerCase().includes('otwarty') || status.toLowerCase().includes('open');
  }

  /**
   * Check if the day is currently closed.
   */
  async isDayClosed(): Promise<boolean> {
    const status = await this.getDayStatus();
    return status.toLowerCase().includes('zamkniety') || status.toLowerCase().includes('closed');
  }

  /**
   * Get the count of recent days displayed in the table.
   */
  async getRecentDaysCount(): Promise<number> {
    const rows = this.recentDaysTableBody.locator('tr');
    return rows.count();
  }

  /**
   * Get recent day data by row index (0-based).
   */
  async getRecentDayData(rowIndex: number): Promise<{ date: string; status: string; sales: string }> {
    const row = this.recentDaysTableBody.locator('tr').nth(rowIndex);
    const cells = row.locator('td');

    return {
      date: (await cells.nth(0).textContent()) || '',
      status: (await cells.nth(1).textContent()) || '',
      sales: (await cells.nth(2).textContent()) || '',
    };
  }

  /**
   * Click manage day button to go to day details.
   */
  async manageDayDetails(): Promise<void> {
    await this.manageDayBtn.click();
    await this.waitForPageLoad();
  }

  /**
   * Wait for the page to be in a ready state.
   */
  async waitForReady(): Promise<void> {
    await this.waitForLoadingComplete();
    // Wait for either open or close button to be visible (use first() to avoid strict mode with .or())
    const openBtnVisible = await this.openDayBtn.isVisible().catch(() => false);
    const closeBtnVisible = await this.closeDayBtn.isVisible().catch(() => false);

    if (!openBtnVisible && !closeBtnVisible) {
      // Wait for at least one button to appear
      await this.page.waitForSelector(
        '[data-testid="open-day-btn"], [data-testid="close-day-btn"]',
        { state: 'visible', timeout: 10000 }
      );
    }
  }

  /**
   * Check if an error is displayed.
   */
  async hasError(): Promise<boolean> {
    return this.errorAlert.isVisible();
  }

  /**
   * Get error message text if visible.
   */
  async getErrorMessage(): Promise<string> {
    if (await this.hasError()) {
      return (await this.errorAlert.textContent()) || '';
    }
    return '';
  }
}
