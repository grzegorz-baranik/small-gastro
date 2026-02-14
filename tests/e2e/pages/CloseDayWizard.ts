import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Close Day Wizard modal.
 * Handles multi-step day closing process with inventory counts.
 */
export class CloseDayWizard extends BasePage {
  // Wizard container
  readonly wizardContainer: Locator;
  readonly wizardStepper: Locator;

  // Navigation buttons
  readonly cancelBtn: Locator;
  readonly backBtn: Locator;
  readonly nextBtn: Locator;
  readonly closeDayBtn: Locator;

  // Closing inventory step
  readonly closingTable: Locator;
  readonly copyExpectedBtn: Locator;

  // Opening inventory step
  readonly openingTable: Locator;
  readonly copyClosingBtn: Locator;

  // Summary step
  readonly summarySection: Locator;
  readonly discrepancySummary: Locator;

  // Error/validation states
  readonly errorMessage: Locator;
  readonly validationErrors: Locator;

  constructor(page: Page) {
    super(page);

    // Wizard container
    this.wizardContainer = page.locator('[data-testid="close-day-wizard"]');
    this.wizardStepper = page.locator('[data-testid="wizard-stepper"]');

    // Navigation buttons
    this.cancelBtn = page.locator('[data-testid="wizard-cancel-btn"]');
    this.backBtn = page.locator('[data-testid="wizard-back-btn"]');
    this.nextBtn = page.locator('[data-testid="wizard-next-btn"]');
    this.closeDayBtn = page.locator('[data-testid="wizard-close-day-btn"]');

    // Closing inventory step
    this.closingTable = page.locator('[data-testid="closing-inventory-table"]');
    this.copyExpectedBtn = page.locator('[data-testid="copy-expected-btn"]');

    // Opening inventory step
    this.openingTable = page.locator('[data-testid="opening-inventory-table"]');
    this.copyClosingBtn = page.locator('[data-testid="copy-closing-btn"]');

    // Summary step
    this.summarySection = page.locator('[data-testid="wizard-summary"]');
    this.discrepancySummary = page.locator('[data-testid="discrepancy-summary"]');

    // Error/validation states
    this.errorMessage = page.locator('[data-testid="wizard-error-message"]');
    this.validationErrors = page.locator('[data-testid="validation-errors"]');
  }

  /**
   * Check if the wizard is visible.
   */
  async isVisible(): Promise<boolean> {
    return this.wizardContainer.isVisible();
  }

  /**
   * Get the current step number (1-based).
   */
  async getCurrentStep(): Promise<number> {
    const steps = this.wizardStepper.locator('button, [role="tab"]');
    const count = await steps.count();

    for (let i = 0; i < count; i++) {
      const step = steps.nth(i);
      const ariaCurrent = await step.getAttribute('aria-current');
      const isActive = await step.getAttribute('data-active');

      if (ariaCurrent === 'step' || isActive === 'true') {
        return i + 1;
      }
    }

    // Fallback: check for active class
    for (let i = 0; i < count; i++) {
      const step = steps.nth(i);
      const classList = await step.getAttribute('class');
      if (classList && (classList.includes('active') || classList.includes('current'))) {
        return i + 1;
      }
    }

    return 1;
  }

  /**
   * Get the total number of steps.
   */
  async getTotalSteps(): Promise<number> {
    const steps = this.wizardStepper.locator('button, [role="tab"]');
    return steps.count();
  }

  /**
   * Go to the next step.
   */
  async goToNextStep(): Promise<void> {
    await this.nextBtn.click();
    await this.page.waitForTimeout(300); // Wait for animation
  }

  /**
   * Go to the previous step.
   */
  async goToPreviousStep(): Promise<void> {
    await this.backBtn.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Enter a closing quantity for a specific ingredient.
   */
  async enterClosingQuantity(ingredientId: number, quantity: string): Promise<void> {
    const input = this.page.locator(`[data-testid="closing-qty-input-${ingredientId}"]`);
    await input.clear();
    await input.fill(quantity);
  }

  /**
   * Enter an opening quantity for a specific ingredient.
   */
  async enterOpeningQuantity(ingredientId: number, quantity: string): Promise<void> {
    const input = this.page.locator(`[data-testid="opening-qty-input-${ingredientId}"]`);
    await input.clear();
    await input.fill(quantity);
  }

  /**
   * Copy expected quantities to closing inventory fields.
   */
  async copyExpectedQuantities(): Promise<void> {
    await this.copyExpectedBtn.click();
    await this.page.waitForTimeout(200);
  }

  /**
   * Copy closing quantities to opening inventory fields.
   */
  async copyClosingQuantities(): Promise<void> {
    await this.copyClosingBtn.click();
    await this.page.waitForTimeout(200);
  }

  /**
   * Get the discrepancy status for a specific ingredient.
   */
  async getDiscrepancyStatus(ingredientId: number): Promise<string> {
    const status = this.page.locator(`[data-testid="closing-status-${ingredientId}"]`);
    return (await status.textContent()) || '';
  }

  /**
   * Get the discrepancy value for a specific ingredient.
   */
  async getDiscrepancyValue(ingredientId: number): Promise<string> {
    const value = this.page.locator(`[data-testid="discrepancy-value-${ingredientId}"]`);
    return (await value.textContent()) || '';
  }

  /**
   * Check if there are any discrepancies.
   */
  async hasDiscrepancies(): Promise<boolean> {
    const discrepancyIndicators = this.closingTable.locator('[data-discrepancy="true"]');
    const count = await discrepancyIndicators.count();
    return count > 0;
  }

  /**
   * Get all ingredient rows from the closing table.
   */
  async getClosingIngredients(): Promise<Array<{ name: string; expected: string; actual: string }>> {
    const rows = this.closingTable.locator('tbody tr');
    const count = await rows.count();
    const ingredients: Array<{ name: string; expected: string; actual: string }> = [];

    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      const name = (await row.locator('[data-testid^="ingredient-name"]').textContent()) || '';
      const expected = (await row.locator('[data-testid^="expected-qty"]').textContent()) || '';
      const actualInput = row.locator('input[data-testid^="closing-qty-input"]');
      const actual = await actualInput.inputValue();

      ingredients.push({ name, expected, actual });
    }

    return ingredients;
  }

  /**
   * Confirm and close the day.
   */
  async confirmClose(): Promise<void> {
    await this.closeDayBtn.click();
    // Wait for and click confirmation dialog if it appears
    const confirmDialog = this.page.locator('[data-testid="confirm-dialog"], [role="alertdialog"]');
    if (await confirmDialog.isVisible({ timeout: 1000 }).catch(() => false)) {
      await this.confirmDialog();
    }
  }

  /**
   * Cancel the wizard.
   */
  async cancel(): Promise<void> {
    await this.cancelBtn.click();
    // Handle potential confirmation dialog for unsaved changes
    const confirmDialog = this.page.locator('[data-testid="confirm-dialog"], [role="alertdialog"]');
    if (await confirmDialog.isVisible({ timeout: 500 }).catch(() => false)) {
      await this.confirmDialog();
    }
  }

  /**
   * Check if the next button is enabled.
   */
  async isNextButtonEnabled(): Promise<boolean> {
    return this.nextBtn.isEnabled();
  }

  /**
   * Check if the close day button is enabled.
   */
  async isCloseDayButtonEnabled(): Promise<boolean> {
    return this.closeDayBtn.isEnabled();
  }

  /**
   * Get error message if visible.
   */
  async getErrorMessage(): Promise<string> {
    if (await this.errorMessage.isVisible()) {
      return (await this.errorMessage.textContent()) || '';
    }
    return '';
  }

  /**
   * Get all validation errors.
   */
  async getValidationErrors(): Promise<string[]> {
    const errors = this.validationErrors.locator('li, p');
    const count = await errors.count();
    const errorTexts: string[] = [];

    for (let i = 0; i < count; i++) {
      const text = await errors.nth(i).textContent();
      if (text) {
        errorTexts.push(text);
      }
    }

    return errorTexts;
  }

  /**
   * Wait for the wizard to be ready.
   */
  async waitForReady(): Promise<void> {
    await expect(this.wizardContainer).toBeVisible({ timeout: 5000 });
    await this.page.waitForTimeout(300); // Wait for animation
  }

  /**
   * Complete the full wizard flow with default values (copy expected to closing, copy closing to opening).
   */
  async completeWithDefaults(): Promise<void> {
    // Step 1: Closing inventory - copy expected values
    await this.copyExpectedQuantities();
    await this.goToNextStep();

    // Step 2: Opening inventory - copy closing values
    await this.copyClosingQuantities();
    await this.goToNextStep();

    // Step 3: Summary - confirm
    await this.confirmClose();
  }
}
