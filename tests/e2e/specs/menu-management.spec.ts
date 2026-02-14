import { test, expect } from '../fixtures/api.fixture';
import { MenuPage } from '../pages/MenuPage';

/**
 * E2E Test: Menu Management
 *
 * Tests creating a product with ingredients:
 * 1. Create ingredients via API
 * 2. Navigate to /menu
 * 3. Click Add Product
 * 4. Fill name and price
 * 5. Save and verify product appears
 *
 * Target: < 30 seconds execution time
 */
test.describe('Menu Management @critical', () => {
  // Test data
  let ingredientMeat: { id: number; name: string };
  let ingredientBread: { id: number; name: string };
  const testProductName = `E2E Kebab ${Date.now()}`;
  const testProductPrice = '25.50';

  test.beforeAll(async ({ api }) => {
    // Create test ingredients
    ingredientMeat = await api.createIngredient({
      name: `E2E Test Meat ${Date.now()}`,
      unit_type: 'weight',
      unit_label: 'g',
    });

    ingredientBread = await api.createIngredient({
      name: `E2E Test Pita ${Date.now()}`,
      unit_type: 'count',
      unit_label: 'szt',
    });
  });

  test('should create a new product', async ({ page }) => {
    const menuPage = new MenuPage(page);

    // Navigate to menu page
    await menuPage.goto();
    await menuPage.waitForPageLoad();

    // Get initial product count
    const initialCount = await menuPage.getProductCount().catch(() => 0);

    // Open add product form
    await menuPage.openAddProductForm();

    // Fill in product details
    await menuPage.productNameInput.fill(testProductName);
    await menuPage.productPriceInput.fill(testProductPrice);

    // Save the product
    await menuPage.saveProductBtn.click();
    await menuPage.waitForPageLoad();

    // Verify product was created
    await expect(menuPage.productsTable.locator(`text=${testProductName}`)).toBeVisible({
      timeout: 5000,
    });

    // Verify product count increased
    const finalCount = await menuPage.getProductCount();
    expect(finalCount).toBeGreaterThan(initialCount);
  });

  test('should create product via API and verify it appears in UI', async ({ page, api }) => {
    const uniqueName = `E2E API Product ${Date.now()}`;

    // Create product via API with ingredients
    await api.createProduct({
      name: uniqueName,
      price_pln: 18.99,
      ingredients: [
        { ingredient_id: ingredientMeat.id, quantity: 150, is_primary: true },
        { ingredient_id: ingredientBread.id, quantity: 1, is_primary: false },
      ],
    });

    const menuPage = new MenuPage(page);

    // Navigate to menu page
    await menuPage.goto();
    await menuPage.waitForPageLoad();

    // Verify product appears in the list
    await expect(menuPage.productsTable.locator(`text=${uniqueName}`)).toBeVisible({
      timeout: 5000,
    });
  });

  test('should display product details correctly', async ({ page, api }) => {
    const uniqueName = `E2E Detail Product ${Date.now()}`;
    const price = 32.5;

    // Create product via API
    await api.createProduct({
      name: uniqueName,
      price_pln: price,
    });

    const menuPage = new MenuPage(page);

    // Navigate to menu page
    await menuPage.goto();
    await menuPage.waitForPageLoad();

    // Find the product row
    const productRow = menuPage.productsTable.locator(`[data-testid^="product-row-"]`).filter({
      hasText: uniqueName,
    });

    // Verify product name is displayed
    await expect(productRow).toBeVisible();
    await expect(productRow).toContainText(uniqueName);

    // Verify price is displayed (formatted as PLN)
    await expect(productRow).toContainText('32,50');
  });

  test('should switch between products and ingredients tabs', async ({ page }) => {
    const menuPage = new MenuPage(page);

    // Navigate to menu page
    await menuPage.goto();
    await menuPage.waitForPageLoad();

    // Verify products tab is active by default
    await expect(menuPage.productsTable).toBeVisible();

    // Switch to ingredients tab
    const ingredientsTab = page.locator('button:has-text("Skladniki"), button:has-text("Skladnik")');
    if (await ingredientsTab.isVisible()) {
      await ingredientsTab.click();
      await menuPage.waitForPageLoad();

      // Switch back to products tab
      const productsTab = page.locator('button:has-text("Produkty"), button:has-text("Produkt")');
      await productsTab.click();
      await menuPage.waitForPageLoad();

      // Verify products table is visible again
      await expect(menuPage.productsTable).toBeVisible();
    }
  });

  test('should validate required fields when creating product', async ({ page }) => {
    const menuPage = new MenuPage(page);

    // Navigate to menu page
    await menuPage.goto();
    await menuPage.waitForPageLoad();

    // Open add product form
    await menuPage.openAddProductForm();

    // Try to save without filling required fields
    await menuPage.saveProductBtn.click();

    // Form should still be visible (not submitted due to HTML5 validation)
    await expect(menuPage.productNameInput).toBeVisible();

    // Fill name but leave price empty
    await menuPage.productNameInput.fill('Test Product');
    await menuPage.saveProductBtn.click();

    // Form should still be visible
    await expect(menuPage.productPriceInput).toBeVisible();
  });
});
