import { test, expect } from '../fixtures/api.fixture';
import { DailyOperationsPage } from '../pages/DailyOperationsPage';
import { CloseDayWizard } from '../pages/CloseDayWizard';

/**
 * E2E Test: Day Closing Wizard
 *
 * Tests the complete day closing wizard flow:
 * 1. Create ingredients via API
 * 2. Open day with inventory via API
 * 3. Navigate through wizard steps 1-4
 * 4. Enter closing quantities
 * 5. Confirm and verify day is closed
 *
 * Target: < 30 seconds execution time
 */
test.describe.configure({ mode: 'serial' });
test.describe('Day Closing Wizard @critical', () => {
  // Test data
  let ingredientMeat: { id: number; name: string };
  let ingredientBread: { id: number; name: string };
  let dailyRecordId: number;

  test.beforeAll(async ({ api }) => {
    // Create test ingredients
    ingredientMeat = await api.createIngredient({
      name: `E2E Meat ${Date.now()}`,
      unit_type: 'weight',
      unit_label: 'kg',
    });

    ingredientBread = await api.createIngredient({
      name: `E2E Bread ${Date.now()}`,
      unit_type: 'count',
      unit_label: 'szt',
    });
  });

  test.beforeEach(async ({ api }) => {
    // Delete any existing day record for today (to ensure clean slate)
    await api.ensureDayDeleted();

    // Open a fresh day with initial inventory
    const today = new Date().toISOString().split('T')[0];
    const record = await api.openDay({
      date: today,
      opening_inventory: [
        { ingredient_id: ingredientMeat.id, quantity: '10.0' },
        { ingredient_id: ingredientBread.id, quantity: '50' },
      ],
    });
    dailyRecordId = record.id;
  });

  test('should complete full day closing wizard flow', async ({ page }) => {
    const dailyOps = new DailyOperationsPage(page);
    const wizard = new CloseDayWizard(page);

    // Navigate to daily operations page
    await dailyOps.goto();
    await dailyOps.waitForReady();

    // Verify day is open
    await expect(dailyOps.closeDayBtn).toBeEnabled();

    // Start close day wizard
    await dailyOps.startCloseDay();
    await wizard.waitForReady();

    // Verify wizard is visible
    await expect(wizard.wizardContainer).toBeVisible();

    // Step 1: Opening Inventory Review
    // This step shows the opening inventory - just click next
    await wizard.goToNextStep();

    // Step 2: Events Review (deliveries, transfers, spoilage)
    // This step shows mid-day events - click next
    await wizard.goToNextStep();

    // Step 3: Closing Inventory
    // Copy expected values (simulates clicking "Copy Expected" button)
    if (await wizard.copyExpectedBtn.isVisible()) {
      await wizard.copyExpectedQuantities();
    } else {
      // Manually enter closing quantities
      await wizard.enterClosingQuantity(ingredientMeat.id, '8.5');
      await wizard.enterClosingQuantity(ingredientBread.id, '45');
    }

    // Proceed to reconciliation
    await wizard.goToNextStep();

    // Step 4: Reconciliation
    // This step shows discrepancies - click next
    await wizard.goToNextStep();

    // Step 5: Confirmation
    // Verify close day button is visible and enabled
    await expect(wizard.closeDayBtn).toBeVisible();
    await expect(wizard.closeDayBtn).toBeEnabled({ timeout: 5000 });

    // Confirm close day
    await wizard.confirmClose();

    // Wait for wizard to close and page to update
    await expect(wizard.wizardContainer).not.toBeVisible({ timeout: 10000 });

    // Verify day is now closed - closeDayBtn should be disabled
    await dailyOps.waitForReady();
    await expect(dailyOps.closeDayBtn).toBeDisabled({ timeout: 5000 });
  });

  test('should navigate back and forth through wizard steps', async ({ page }) => {
    const dailyOps = new DailyOperationsPage(page);
    const wizard = new CloseDayWizard(page);

    // Navigate to daily operations and start wizard
    await dailyOps.goto();
    await dailyOps.waitForReady();
    await dailyOps.startCloseDay();
    await wizard.waitForReady();

    // Go to step 2
    await wizard.goToNextStep();

    // Go back to step 1
    await expect(wizard.backBtn).toBeVisible();
    await wizard.goToPreviousStep();

    // Verify we can still proceed forward
    await expect(wizard.nextBtn).toBeEnabled();
  });

  test('should allow canceling the wizard', async ({ page }) => {
    const dailyOps = new DailyOperationsPage(page);
    const wizard = new CloseDayWizard(page);

    // Navigate to daily operations and start wizard
    await dailyOps.goto();
    await dailyOps.waitForReady();
    await dailyOps.startCloseDay();
    await wizard.waitForReady();

    // Cancel the wizard
    await wizard.cancel();

    // Verify wizard is closed
    await expect(wizard.wizardContainer).not.toBeVisible({ timeout: 5000 });

    // Verify day is still open
    await dailyOps.waitForReady();
    await expect(dailyOps.closeDayBtn).toBeEnabled();
  });
});
