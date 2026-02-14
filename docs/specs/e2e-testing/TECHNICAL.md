# E2E Testing - Technical Design

## Status: Draft
**Created**: 2026-01-06
**Last Updated**: 2026-01-06

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Playwright Test Runner                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Test Specs  │  │ Page Objects│  │ Fixtures (API/DB)       │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Frontend   │  │   Backend    │  │  PostgreSQL  │           │
│  │  (port 8304) │  │  (port 8303) │  │  (port 5461) │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation & Setup

### 1. Install Playwright

```bash
# From project root
cd tests/e2e
npm init -y
npm install -D @playwright/test
npx playwright install chromium webkit
```

### 2. Package.json Scripts

```json
{
  "name": "small-gastro-e2e",
  "scripts": {
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug",
    "test:ui": "playwright test --ui",
    "test:chromium": "playwright test --project=chromium",
    "test:webkit": "playwright test --project=webkit",
    "report": "playwright show-report"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

---

## Configuration

### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list']
  ],

  use: {
    baseURL: 'http://localhost:8304',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // Global setup for database initialization
  globalSetup: require.resolve('./global-setup.ts'),
});
```

---

## Global Setup

### global-setup.ts

```typescript
import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  // Verify Docker stack is running
  const healthCheck = await fetch('http://localhost:8303/api/v1/health');
  if (!healthCheck.ok) {
    throw new Error('Backend not running. Start with: docker compose up -d');
  }

  console.log('✓ Backend health check passed');
}

export default globalSetup;
```

---

## Fixtures

### fixtures/api.fixture.ts

```typescript
import { test as base, APIRequestContext } from '@playwright/test';

// API helper class
export class ApiHelper {
  constructor(private request: APIRequestContext) {}

  // Ingredients
  async createIngredient(data: {
    name: string;
    unit_type: 'weight' | 'count';
    current_stock?: number;
  }) {
    const response = await this.request.post('/api/v1/ingredients', { data });
    expect(response.ok()).toBeTruthy();
    return response.json();
  }

  async deleteIngredient(id: number) {
    await this.request.delete(`/api/v1/ingredients/${id}`);
  }

  // Products
  async createProduct(data: {
    name: string;
    price: number;
    ingredients?: Array<{ ingredient_id: number; quantity: number }>;
  }) {
    const response = await this.request.post('/api/v1/products', { data });
    expect(response.ok()).toBeTruthy();
    return response.json();
  }

  // Daily Records
  async openDay(data: {
    date: string;
    opening_inventory: Array<{ ingredient_id: number; quantity: number }>;
  }) {
    const response = await this.request.post('/api/v1/daily-records/open', { data });
    expect(response.ok()).toBeTruthy();
    return response.json();
  }

  async getOpenDay() {
    const response = await this.request.get('/api/v1/daily-records/status/open');
    if (response.status() === 404) return null;
    return response.json();
  }

  // Employees
  async createEmployee(data: {
    first_name: string;
    last_name: string;
    position_id?: number;
  }) {
    const response = await this.request.post('/api/v1/employees', { data });
    expect(response.ok()).toBeTruthy();
    return response.json();
  }

  // Categories
  async createCategory(data: {
    name: string;
    parent_id?: number;
  }) {
    const response = await this.request.post('/api/v1/categories', { data });
    expect(response.ok()).toBeTruthy();
    return response.json();
  }

  // Transactions
  async createExpense(data: {
    category_id: number;
    amount: number;
    description?: string;
    daily_record_id?: number;
  }) {
    const response = await this.request.post('/api/v1/transactions', {
      data: { ...data, type: 'expense' }
    });
    expect(response.ok()).toBeTruthy();
    return response.json();
  }

  // Cleanup
  async resetDatabase() {
    // Call a special test endpoint or use direct DB connection
    await this.request.post('/api/v1/test/reset-database');
  }
}

// Extended test fixture
export const test = base.extend<{ api: ApiHelper }>({
  api: async ({ request }, use) => {
    const api = new ApiHelper(request);
    await use(api);
  },
});

export { expect } from '@playwright/test';
```

### fixtures/database.fixture.ts

```typescript
import { test as base } from '@playwright/test';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function resetDatabase() {
  // Option 1: Docker exec to run migrations fresh
  await execAsync(
    'docker compose exec -T backend alembic downgrade base && ' +
    'docker compose exec -T backend alembic upgrade head'
  );

  // Option 2: Use a test reset endpoint (if implemented)
  // await fetch('http://localhost:8303/api/v1/test/reset');
}

export async function seedTestData(apiRequest: any) {
  // Create base test data needed by multiple tests
  const ingredients = [
    { name: 'Mięso kebab', unit_type: 'weight' },
    { name: 'Bułki', unit_type: 'count' },
    { name: 'Sałata', unit_type: 'weight' },
    { name: 'Pomidory', unit_type: 'weight' },
  ];

  const createdIngredients = [];
  for (const ing of ingredients) {
    const response = await apiRequest.post('/api/v1/ingredients', { data: ing });
    createdIngredients.push(await response.json());
  }

  return { ingredients: createdIngredients };
}
```

---

## Page Object Model

### pages/BasePage.ts

```typescript
import { Page, Locator } from '@playwright/test';

export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Common navigation
  async navigateTo(path: string) {
    await this.page.goto(path);
  }

  // Common waits
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  // Common assertions
  async expectToastMessage(text: string) {
    await this.page.locator('.toast, [role="alert"]').filter({ hasText: text }).waitFor();
  }

  // Modal helpers
  async isModalVisible(): Promise<boolean> {
    return this.page.locator('[role="dialog"], .modal').isVisible();
  }

  async closeModal() {
    await this.page.keyboard.press('Escape');
  }
}
```

### pages/DailyOperationsPage.ts

```typescript
import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class DailyOperationsPage extends BasePage {
  // Locators
  readonly openDayButton: Locator;
  readonly closeDayButton: Locator;
  readonly recentDaysTable: Locator;
  readonly statusBadge: Locator;

  constructor(page: Page) {
    super(page);
    this.openDayButton = page.getByRole('button', { name: /otwórz dzień/i });
    this.closeDayButton = page.getByRole('button', { name: /zamknij dzień/i });
    this.recentDaysTable = page.locator('table');
    this.statusBadge = page.locator('.status-badge, [data-testid="day-status"]');
  }

  async goto() {
    await this.navigateTo('/operacje');
    await this.waitForPageLoad();
  }

  async openDay() {
    await this.openDayButton.click();
    // Wait for modal
    await this.page.waitForSelector('[role="dialog"]');
  }

  async startCloseDay() {
    await this.closeDayButton.click();
    // Wait for wizard to appear
    await this.page.waitForSelector('[data-testid="close-day-wizard"]');
  }

  async getDayStatus(): Promise<string> {
    return this.statusBadge.textContent() ?? '';
  }

  async getRecentDaysCount(): Promise<number> {
    const rows = this.recentDaysTable.locator('tbody tr');
    return rows.count();
  }
}
```

### pages/CloseDayWizard.ts

```typescript
import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class CloseDayWizard extends BasePage {
  // Step indicators
  readonly stepIndicator: Locator;
  readonly nextButton: Locator;
  readonly backButton: Locator;
  readonly confirmButton: Locator;

  // Step 1: Opening inventory
  readonly openingInventoryTable: Locator;

  // Step 2: Events
  readonly eventsTable: Locator;

  // Step 3: Closing quantities
  readonly closingForm: Locator;
  readonly copyExpectedButton: Locator;

  // Step 4: Summary
  readonly summarySection: Locator;
  readonly notesInput: Locator;

  constructor(page: Page) {
    super(page);
    this.stepIndicator = page.locator('[data-testid="wizard-step"], .wizard-stepper');
    this.nextButton = page.getByRole('button', { name: /dalej|następny/i });
    this.backButton = page.getByRole('button', { name: /wstecz|poprzedni/i });
    this.confirmButton = page.getByRole('button', { name: /zamknij dzień/i });

    this.openingInventoryTable = page.locator('[data-testid="opening-inventory"]');
    this.eventsTable = page.locator('[data-testid="events-table"]');
    this.closingForm = page.locator('[data-testid="closing-form"]');
    this.copyExpectedButton = page.getByRole('button', { name: /kopiuj oczekiwane/i });
    this.summarySection = page.locator('[data-testid="summary"]');
    this.notesInput = page.locator('textarea[name="notes"]');
  }

  async getCurrentStep(): Promise<number> {
    const activeStep = this.stepIndicator.locator('.active, [aria-current="step"]');
    const stepText = await activeStep.textContent();
    return parseInt(stepText?.match(/\d+/)?.[0] ?? '1');
  }

  async goToNextStep() {
    await this.nextButton.click();
    await this.page.waitForTimeout(300); // Animation
  }

  async goToPreviousStep() {
    await this.backButton.click();
    await this.page.waitForTimeout(300);
  }

  async enterClosingQuantity(ingredientName: string, quantity: string) {
    const row = this.closingForm.locator(`tr:has-text("${ingredientName}")`);
    const input = row.locator('input[type="number"]');
    await input.fill(quantity);
  }

  async copyExpectedQuantities() {
    await this.copyExpectedButton.click();
  }

  async addNotes(notes: string) {
    await this.notesInput.fill(notes);
  }

  async confirmClose() {
    await this.confirmButton.click();
    // Wait for confirmation dialog
    await this.page.getByRole('button', { name: /potwierdź/i }).click();
  }

  async getDiscrepancyStatus(ingredientName: string): Promise<string> {
    const row = this.closingForm.locator(`tr:has-text("${ingredientName}")`);
    const statusCell = row.locator('[data-testid="discrepancy-status"]');
    return statusCell.textContent() ?? '';
  }
}
```

### pages/MenuPage.ts

```typescript
import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class MenuPage extends BasePage {
  readonly addProductButton: Locator;
  readonly productsTable: Locator;
  readonly productNameInput: Locator;
  readonly productPriceInput: Locator;
  readonly addIngredientButton: Locator;
  readonly saveButton: Locator;

  constructor(page: Page) {
    super(page);
    this.addProductButton = page.getByRole('button', { name: /dodaj produkt/i });
    this.productsTable = page.locator('table');
    this.productNameInput = page.locator('input[name="name"]');
    this.productPriceInput = page.locator('input[name="price"]');
    this.addIngredientButton = page.getByRole('button', { name: /dodaj składnik/i });
    this.saveButton = page.getByRole('button', { name: /zapisz/i });
  }

  async goto() {
    await this.navigateTo('/menu');
    await this.waitForPageLoad();
  }

  async createProduct(name: string, price: number) {
    await this.addProductButton.click();
    await this.productNameInput.fill(name);
    await this.productPriceInput.fill(price.toString());
    await this.saveButton.click();
  }

  async addIngredientToProduct(ingredientName: string, quantity: string) {
    await this.addIngredientButton.click();
    await this.page.selectOption('[name="ingredient"]', { label: ingredientName });
    await this.page.fill('[name="quantity"]', quantity);
  }

  async getProductCount(): Promise<number> {
    return this.productsTable.locator('tbody tr').count();
  }

  async productExists(name: string): Promise<boolean> {
    return this.productsTable.locator(`text=${name}`).isVisible();
  }
}
```

---

## Test Specifications

### specs/day-closing.spec.ts

```typescript
import { test, expect } from '../fixtures/api.fixture';
import { DailyOperationsPage } from '../pages/DailyOperationsPage';
import { CloseDayWizard } from '../pages/CloseDayWizard';

test.describe('Day Closing Wizard', () => {
  let dailyOps: DailyOperationsPage;
  let wizard: CloseDayWizard;

  test.beforeEach(async ({ page, api }) => {
    dailyOps = new DailyOperationsPage(page);
    wizard = new CloseDayWizard(page);

    // Setup: Create ingredients and open day
    const meat = await api.createIngredient({ name: 'Mięso kebab', unit_type: 'weight' });
    const buns = await api.createIngredient({ name: 'Bułki', unit_type: 'count' });

    await api.openDay({
      date: new Date().toISOString().split('T')[0],
      opening_inventory: [
        { ingredient_id: meat.id, quantity: 5.0 },
        { ingredient_id: buns.id, quantity: 50 },
      ]
    });
  });

  test('should complete full day closing flow', async ({ page }) => {
    // Navigate to daily operations
    await dailyOps.goto();

    // Start closing wizard
    await dailyOps.startCloseDay();

    // Step 1: Review opening inventory
    expect(await wizard.getCurrentStep()).toBe(1);
    await expect(wizard.openingInventoryTable).toContainText('Mięso kebab');
    await expect(wizard.openingInventoryTable).toContainText('5');
    await wizard.goToNextStep();

    // Step 2: Review events (empty in this test)
    expect(await wizard.getCurrentStep()).toBe(2);
    await wizard.goToNextStep();

    // Step 3: Enter closing quantities
    expect(await wizard.getCurrentStep()).toBe(3);
    await wizard.enterClosingQuantity('Mięso kebab', '4.5');
    await wizard.enterClosingQuantity('Bułki', '45');
    await wizard.goToNextStep();

    // Step 4: Confirm
    expect(await wizard.getCurrentStep()).toBe(4);
    await wizard.addNotes('Test day closing');
    await wizard.confirmClose();

    // Verify day is closed
    await expect(page.locator('.status-badge')).toContainText(/zamknięt/i);
  });

  test('should navigate back and forth between steps', async ({ page }) => {
    await dailyOps.goto();
    await dailyOps.startCloseDay();

    // Forward
    expect(await wizard.getCurrentStep()).toBe(1);
    await wizard.goToNextStep();
    expect(await wizard.getCurrentStep()).toBe(2);

    // Backward
    await wizard.goToPreviousStep();
    expect(await wizard.getCurrentStep()).toBe(1);
  });

  test('should copy expected quantities to closing form', async ({ page }) => {
    await dailyOps.goto();
    await dailyOps.startCloseDay();

    // Navigate to step 3
    await wizard.goToNextStep();
    await wizard.goToNextStep();

    // Copy expected values
    await wizard.copyExpectedQuantities();

    // Verify values were copied
    const meatInput = page.locator('tr:has-text("Mięso kebab") input');
    await expect(meatInput).toHaveValue('5');
  });

  test('should reject negative closing quantities', async ({ page }) => {
    await dailyOps.goto();
    await dailyOps.startCloseDay();

    await wizard.goToNextStep();
    await wizard.goToNextStep();

    await wizard.enterClosingQuantity('Mięso kebab', '-1');

    // Should show validation error
    await expect(page.locator('.error, [role="alert"]')).toBeVisible();
  });
});
```

### specs/menu-management.spec.ts

```typescript
import { test, expect } from '../fixtures/api.fixture';
import { MenuPage } from '../pages/MenuPage';

test.describe('Menu Management', () => {
  let menuPage: MenuPage;

  test.beforeEach(async ({ page, api }) => {
    menuPage = new MenuPage(page);

    // Setup: Create base ingredients
    await api.createIngredient({ name: 'Mięso wołowe', unit_type: 'weight' });
    await api.createIngredient({ name: 'Bułka burger', unit_type: 'count' });
  });

  test('should create product with price', async ({ page }) => {
    await menuPage.goto();

    const initialCount = await menuPage.getProductCount();
    await menuPage.createProduct('Burger klasyczny', 18.50);

    expect(await menuPage.getProductCount()).toBe(initialCount + 1);
    expect(await menuPage.productExists('Burger klasyczny')).toBeTruthy();
  });

  test('should add ingredients to product', async ({ page }) => {
    await menuPage.goto();
    await menuPage.addProductButton.click();

    await menuPage.productNameInput.fill('Burger z mięsem');
    await menuPage.productPriceInput.fill('22.00');

    await menuPage.addIngredientToProduct('Mięso wołowe', '0.15');
    await menuPage.addIngredientToProduct('Bułka burger', '1');

    await menuPage.saveButton.click();

    // Verify product has ingredients
    await page.click('text=Burger z mięsem');
    await expect(page.locator('.ingredients-list')).toContainText('Mięso wołowe');
    await expect(page.locator('.ingredients-list')).toContainText('0.15 kg');
  });
});
```

---

## Running Tests

### Local Development

```bash
# Ensure Docker stack is running
docker compose up -d

# Wait for services
docker compose exec backend alembic upgrade head

# Run all tests
cd tests/e2e
npm test

# Run specific test file
npm test -- specs/day-closing.spec.ts

# Run with UI for debugging
npm run test:ui

# Run headed (see browser)
npm run test:headed
```

### Test Reports

```bash
# Generate HTML report
npm test

# View report
npm run report
# Opens: tests/e2e/playwright-report/index.html
```

---

## Future Enhancements

### Phase 2: CI/CD Integration

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start Docker stack
        run: docker compose up -d
      - name: Wait for services
        run: |
          docker compose exec -T backend alembic upgrade head
          sleep 5
      - name: Run Playwright tests
        run: |
          cd tests/e2e
          npm ci
          npx playwright install --with-deps
          npm test
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

### Phase 3: Visual Testing

Add visual regression with Playwright's screenshot comparison:
```typescript
await expect(page).toHaveScreenshot('day-closing-step-1.png');
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| @playwright/test | ^1.40.0 | Test framework |
| playwright | ^1.40.0 | Browser automation |

---

## Related Documents

- [README.md](./README.md) - Functional specification
- [scenarios.feature](./scenarios.feature) - BDD scenarios
- [TESTING.md](./TESTING.md) - Test execution plan
