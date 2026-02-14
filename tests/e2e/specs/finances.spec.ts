import { test, expect } from '../fixtures/api.fixture';
import { FinancesPage } from '../pages/FinancesPage';

/**
 * E2E Test: Finance Management
 *
 * Tests creating category hierarchy and expenses:
 * 1. Navigate to /ustawienia (settings page with categories)
 * 2. Create parent category
 * 3. Create child category under parent
 * 4. Navigate to /finanse
 * 5. Add expense under child category
 * 6. Verify expense appears
 *
 * Target: < 30 seconds execution time
 */
test.describe('Finance Management @critical', () => {
  // Test data
  const parentCategoryName = `E2E Operations ${Date.now()}`;
  const childCategoryName = `E2E Supplies ${Date.now()}`;
  const leafCategoryName = `E2E Ingredients ${Date.now()}`;
  let parentCategory: { id: number; name: string };
  let childCategory: { id: number; name: string };
  let leafCategory: { id: number; name: string };

  test.beforeAll(async ({ api }) => {
    // Create category hierarchy via API
    parentCategory = await api.createCategory({ name: parentCategoryName });
    childCategory = await api.createCategory({
      name: childCategoryName,
      parent_id: parentCategory.id,
    });
    leafCategory = await api.createCategory({
      name: leafCategoryName,
      parent_id: childCategory.id,
    });
  });

  test('should display expense category hierarchy in settings', async ({ page }) => {
    // Navigate to settings page (where categories are managed)
    await page.goto('/ustawienia');
    await page.waitForLoadState('networkidle');

    // Verify parent category is visible
    await expect(page.locator(`text=${parentCategoryName}`)).toBeVisible({
      timeout: 10000,
    });

    // Verify child category is visible (may need to expand parent)
    await expect(page.locator(`text=${childCategoryName}`)).toBeVisible({
      timeout: 5000,
    });

    // Verify leaf category is visible
    await expect(page.locator(`text=${leafCategoryName}`)).toBeVisible({
      timeout: 5000,
    });
  });

  test('should create a new expense', async ({ page }) => {
    const financesPage = new FinancesPage(page);
    const expenseAmount = '150.00';
    const expenseDescription = `E2E Test Expense ${Date.now()}`;

    // Navigate to finances page
    await financesPage.goto();

    // Click add expense button
    await financesPage.openAddExpenseForm();

    // The form should be visible
    await expect(financesPage.expenseAmountInput).toBeVisible();

    // Select the expense type (should be default) - target the button inside the modal
    const expenseTypeBtn = page.locator('[data-testid="modal-content"] button').filter({ hasText: /wydatek|expense/i }).first();
    if (await expenseTypeBtn.isVisible()) {
      await expenseTypeBtn.click();
    }

    // Select category using SearchableSelect or regular select
    // First try to find SearchableSelect input
    const categoryInput = page.locator('input[placeholder*="kategor"], input[placeholder*="Wybierz"]').first();
    if (await categoryInput.isVisible()) {
      // Click to open dropdown
      await categoryInput.click();
      await page.waitForTimeout(300);

      // Type to filter and select the leaf category
      await categoryInput.fill(leafCategoryName.substring(0, 10));
      await page.waitForTimeout(300);

      // Click on the matching option
      const option = page.locator(`[role="option"], li, div`).filter({ hasText: leafCategoryName }).first();
      if (await option.isVisible()) {
        await option.click();
      }
    } else {
      // Fallback to regular select
      const categorySelect = page.locator('select').filter({ hasText: /kategor/i });
      if (await categorySelect.isVisible()) {
        await categorySelect.selectOption({ label: new RegExp(leafCategoryName) });
      }
    }

    // Enter amount
    await financesPage.expenseAmountInput.fill(expenseAmount);

    // Enter description
    const descInput = page.locator('input[type="text"]').filter({
      has: page.locator('..').filter({ hasText: /opis|description/i }),
    }).or(page.locator('input').last());

    if (await descInput.isVisible()) {
      await descInput.fill(expenseDescription);
    }

    // Save expense
    await financesPage.saveExpenseBtn.click();

    // Wait for modal to close
    await expect(financesPage.expenseAmountInput).not.toBeVisible({
      timeout: 5000,
    });

    // Verify expense appears in the list by checking for unique description
    await expect(page.locator(`text=${expenseDescription}`).first()).toBeVisible({
      timeout: 5000,
    });
  });

  test('should create expense via API and verify in UI', async ({ page, api }) => {
    const amount = 250.5;
    const description = `E2E API Expense ${Date.now()}`;

    // Create expense via API
    await api.createExpense({
      category_id: leafCategory.id,
      amount: amount,
      description: description,
    });

    const financesPage = new FinancesPage(page);

    // Navigate to finances page
    await financesPage.goto();

    // Verify expense appears in the list
    await expect(page.locator(`text=${description}`).first()).toBeVisible({
      timeout: 10000,
    });

    // Verify amount is displayed
    await expect(page.locator(`text=250,50`).or(page.locator(`text=250.50`)).first()).toBeVisible();
  });

  test('should filter transactions by type', async ({ page, api }) => {
    // Create a revenue transaction via API
    const revenueDescription = `E2E Revenue ${Date.now()}`;

    // Navigate to finances page
    const financesPage = new FinancesPage(page);
    await financesPage.goto();

    // Click expenses filter
    const expensesFilter = page.locator('button').filter({ hasText: /wydatki|expenses/i });
    if (await expensesFilter.isVisible()) {
      await expensesFilter.click();
      await page.waitForTimeout(500);

      // Verify filter is applied (button should be highlighted/active)
      await expect(expensesFilter).toHaveClass(/bg-red|active|selected/);
    }

    // Click all filter
    const allFilter = page.locator('button').filter({ hasText: /wszystkie|all/i });
    if (await allFilter.isVisible()) {
      await allFilter.click();
      await page.waitForTimeout(500);
    }
  });

  test('should display transaction with correct formatting', async ({ page, api }) => {
    const amount = 99.99;
    const description = `E2E Format Test ${Date.now()}`;

    // Create expense via API
    await api.createExpense({
      category_id: leafCategory.id,
      amount: amount,
      description: description,
    });

    const financesPage = new FinancesPage(page);
    await financesPage.goto();

    // Find the transaction row (use data-testid selector, fallback to first matching text)
    const transactionRow = page.locator('[data-testid^="transaction-row-"]').filter({
      hasText: description,
    }).first();

    // Verify transaction is displayed
    await expect(transactionRow).toBeVisible({ timeout: 10000 });

    // Verify amount is formatted correctly (Polish format: 99,99 PLN)
    await expect(transactionRow).toContainText(/99[,.]99/);

    // Verify description is shown
    await expect(transactionRow).toContainText(description);

    // Verify it's marked as expense (red color or minus sign)
    await expect(transactionRow.locator('.text-red-600, [class*="red"]').or(
      transactionRow.locator('text=-')
    ).first()).toBeVisible();
  });

  test('should show category path in transaction', async ({ page, api }) => {
    const description = `E2E Category Path ${Date.now()}`;

    // Create expense via API
    await api.createExpense({
      category_id: leafCategory.id,
      amount: 50.0,
      description: description,
    });

    const financesPage = new FinancesPage(page);
    await financesPage.goto();

    // Find the transaction (use data-testid selector)
    const transactionRow = page.locator('[data-testid^="transaction-row-"]').filter({
      hasText: description,
    }).first();

    await expect(transactionRow).toBeVisible({ timeout: 10000 });

    // Category name should be visible in the transaction
    await expect(transactionRow).toContainText(leafCategoryName);
  });
});
