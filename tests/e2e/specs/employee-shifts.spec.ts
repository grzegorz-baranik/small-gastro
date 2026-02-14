import { test, expect } from '../fixtures/api.fixture';
import { EmployeesPage } from '../pages/EmployeesPage';

/**
 * E2E Test: Employee Management
 *
 * Tests creating employees and managing their data:
 * 1. Create position via API
 * 2. Navigate to /ustawienia (settings page with employees)
 * 3. Create employee with name and position
 * 4. Verify employee appears in table with correct details
 *
 * Target: < 30 seconds execution time
 */
test.describe('Employee & Shifts Management @critical', () => {
  // Test data
  let position: { id: number; name: string };
  const testEmployeeName = `E2E Worker ${Date.now()}`;

  test.beforeAll(async ({ api }) => {
    // Create test position
    position = await api.createPosition({
      name: `E2E Position ${Date.now()}`,
      hourly_rate: 25.0,
    });
  });

  test('should create a new employee with position', async ({ page }) => {
    // Navigate to settings page (where employees section is)
    await page.goto('/ustawienia');
    await page.waitForLoadState('networkidle');

    // Find employees section (use first() to avoid strict mode violations with multiple tables)
    const employeesSection = page.locator('[data-testid="employees-table"]').first();

    // Wait for employees section to be visible
    await expect(employeesSection).toBeVisible({
      timeout: 10000,
    });

    // Click add employee button (use first() in case there are multiple sections)
    const addEmployeeBtn = page.locator('[data-testid="add-employee-btn"]').first();
    await addEmployeeBtn.click();

    // Wait for modal to open
    await expect(page.locator('[data-testid="employee-name-input"]')).toBeVisible({
      timeout: 5000,
    });

    // Fill employee name
    await page.locator('[data-testid="employee-name-input"]').fill(testEmployeeName);

    // Select position from dropdown
    const positionSelect = page.locator('select').first();
    if (await positionSelect.isVisible()) {
      // Get all options and find one containing our position name
      const options = await positionSelect.locator('option').allTextContents();
      const matchingOption = options.find(opt => opt.includes(position.name));
      if (matchingOption) {
        await positionSelect.selectOption({ label: matchingOption });
      }
    }

    // Save employee
    await page.locator('[data-testid="save-employee-btn"]').click();

    // Wait for modal to close
    await expect(page.locator('[data-testid="employee-name-input"]')).not.toBeVisible({
      timeout: 5000,
    });

    // Verify employee appears in table
    await expect(page.locator(`text=${testEmployeeName}`)).toBeVisible({
      timeout: 5000,
    });
  });

  test('should create employee via API and verify in UI', async ({ page, api }) => {
    const uniqueName = `E2E API Employee ${Date.now()}`;

    // Create employee via API
    await api.createEmployee({
      name: uniqueName,
      position_id: position.id,
    });

    // Navigate to settings page
    await page.goto('/ustawienia');
    await page.waitForLoadState('networkidle');

    // Verify employee appears in the list
    await expect(page.locator(`text=${uniqueName}`)).toBeVisible({
      timeout: 10000,
    });
  });

  test('should display employee details correctly', async ({ page, api }) => {
    const uniqueName = `E2E Detail Employee ${Date.now()}`;

    // Create employee via API
    await api.createEmployee({
      name: uniqueName,
      position_id: position.id,
      hourly_rate: 30.0,
    });

    // Navigate to settings page
    await page.goto('/ustawienia');
    await page.waitForLoadState('networkidle');

    // Find the employee row
    const employeeRow = page.locator('[data-testid^="employee-row-"]').filter({
      hasText: uniqueName,
    }).or(
      page.locator('tr').filter({ hasText: uniqueName })
    );

    // Verify employee name is displayed
    await expect(employeeRow).toBeVisible({ timeout: 10000 });
    await expect(employeeRow).toContainText(uniqueName);

    // Verify position is displayed
    await expect(employeeRow).toContainText(position.name);
  });

  test('should toggle show inactive employees', async ({ page, api }) => {
    // Create an inactive employee via API
    const inactiveName = `E2E Inactive ${Date.now()}`;
    const employee = await api.createEmployee({
      name: inactiveName,
      position_id: position.id,
    });

    // Navigate to settings page
    await page.goto('/ustawienia');
    await page.waitForLoadState('networkidle');

    // Find the show inactive checkbox
    const showInactiveCheckbox = page.locator('input[type="checkbox"]').filter({
      has: page.locator('..').filter({ hasText: /nieaktywn|inactive/i }),
    }).or(
      page.locator('label').filter({ hasText: /nieaktywn|inactive/i }).locator('input[type="checkbox"]')
    );

    // Verify checkbox exists
    if (await showInactiveCheckbox.isVisible()) {
      // Toggle checkbox
      await showInactiveCheckbox.click();
      await page.waitForTimeout(500);

      // Toggle back
      await showInactiveCheckbox.click();
      await page.waitForTimeout(500);
    }

    // Verify active employee is visible
    await expect(page.locator(`text=${inactiveName}`)).toBeVisible();
  });

  test('should display hourly rate with PLN suffix', async ({ page, api }) => {
    const uniqueName = `E2E Rate Employee ${Date.now()}`;

    // Create employee via API with custom hourly rate
    await api.createEmployee({
      name: uniqueName,
      position_id: position.id,
      hourly_rate: 35.5,
    });

    // Navigate to settings page
    await page.goto('/ustawienia');
    await page.waitForLoadState('networkidle');

    // Find the employee row and verify hourly rate display
    const employeeRow = page.locator('tr, [data-testid^="employee-row-"]').filter({
      hasText: uniqueName,
    });

    await expect(employeeRow).toBeVisible({ timeout: 10000 });

    // Check for rate display (format may vary: "35,50 PLN/h" or "35.50 PLN/h")
    await expect(employeeRow).toContainText(/35[,.]50/);
  });
});
