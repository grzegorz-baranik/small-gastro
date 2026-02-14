import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class FinancesPage extends BasePage {
  readonly addExpenseBtn: Locator;
  readonly expenseAmountInput: Locator;
  readonly saveExpenseBtn: Locator;

  constructor(page: Page) {
    super(page);
    this.addExpenseBtn = page.locator('[data-testid="add-expense-btn"]');
    this.expenseAmountInput = page.locator('[data-testid="expense-amount-input"]');
    this.saveExpenseBtn = page.locator('[data-testid="save-expense-btn"]');
  }

  async goto() {
    await this.navigateTo('/finanse');
    await this.waitForPageLoad();
  }

  async openAddExpenseForm() {
    await this.addExpenseBtn.click();
    await this.page.waitForSelector('[data-testid="expense-amount-input"]');
  }

  async createExpense(categoryName: string, amount: string, description?: string) {
    await this.openAddExpenseForm();

    // Select category
    const categorySelect = this.page.locator('select[name="category"], [data-testid*="category-select"]');
    await categorySelect.selectOption({ label: categoryName });

    // Enter amount
    await this.expenseAmountInput.fill(amount);

    // Enter description if provided
    if (description) {
      const descInput = this.page.locator('input[name="description"], textarea[name="description"]');
      await descInput.fill(description);
    }

    await this.saveExpenseBtn.click();
    await this.waitForPageLoad();
  }

  async switchToCategoriesTab() {
    await this.page.click('button:has-text("Kategorie"), [role="tab"]:has-text("Kategorie")');
    await this.waitForPageLoad();
  }

  async createCategory(name: string, parentName?: string) {
    await this.switchToCategoriesTab();

    const addCategoryBtn = this.page.locator('[data-testid="add-category-btn"], button:has-text("Dodaj kategorię")');
    await addCategoryBtn.click();

    const nameInput = this.page.locator('[data-testid="category-name-input"], input[name="name"]');
    await nameInput.fill(name);

    if (parentName) {
      const parentSelect = this.page.locator('select[name="parent"], [data-testid*="parent-select"]');
      await parentSelect.selectOption({ label: parentName });
    }

    const saveBtn = this.page.locator('[data-testid="save-category-btn"], button:has-text("Zapisz")');
    await saveBtn.click();
    await this.waitForPageLoad();
  }
}
