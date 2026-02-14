import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class MenuPage extends BasePage {
  readonly addProductBtn: Locator;
  readonly productsTable: Locator;
  readonly productNameInput: Locator;
  readonly productPriceInput: Locator;
  readonly saveProductBtn: Locator;

  constructor(page: Page) {
    super(page);
    this.addProductBtn = page.locator('[data-testid="add-product-btn"]');
    this.productsTable = page.locator('[data-testid="products-table"]');
    this.productNameInput = page.locator('[data-testid="product-name-input"]');
    this.productPriceInput = page.locator('[data-testid="product-price-input"]');
    this.saveProductBtn = page.locator('[data-testid="save-product-btn"]');
  }

  async goto() {
    await this.navigateTo('/menu');
    await this.waitForPageLoad();
  }

  async openAddProductForm() {
    await this.addProductBtn.click();
    await this.page.waitForSelector('[data-testid="product-name-input"]');
  }

  async createProduct(name: string, price: string) {
    await this.openAddProductForm();
    await this.productNameInput.fill(name);
    await this.productPriceInput.fill(price);
    await this.saveProductBtn.click();
    await this.waitForPageLoad();
  }

  async addIngredientToProduct(ingredientName: string, quantity: string) {
    // Click add ingredient button in the product form
    const addIngBtn = this.page.locator('button:has-text("Dodaj składnik")');
    await addIngBtn.click();

    // Select ingredient from dropdown
    const ingredientSelect = this.page.locator('select[name="ingredient"], [data-testid*="ingredient-select"]').last();
    await ingredientSelect.selectOption({ label: ingredientName });

    // Enter quantity
    const qtyInput = this.page.locator('input[name="quantity"], [data-testid*="ingredient-qty"]').last();
    await qtyInput.fill(quantity);
  }

  async productExists(name: string): Promise<boolean> {
    return this.productsTable.locator(`text=${name}`).isVisible();
  }

  async getProductCount(): Promise<number> {
    const rows = this.productsTable.locator('[data-testid^="product-row-"]');
    return rows.count();
  }
}
