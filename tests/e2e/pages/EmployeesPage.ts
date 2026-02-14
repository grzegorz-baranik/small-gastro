import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class EmployeesPage extends BasePage {
  readonly addEmployeeBtn: Locator;
  readonly employeesTable: Locator;
  readonly employeeNameInput: Locator;
  readonly saveEmployeeBtn: Locator;

  constructor(page: Page) {
    super(page);
    this.addEmployeeBtn = page.locator('[data-testid="add-employee-btn"]');
    this.employeesTable = page.locator('[data-testid="employees-table"]');
    this.employeeNameInput = page.locator('[data-testid="employee-name-input"]');
    this.saveEmployeeBtn = page.locator('[data-testid="save-employee-btn"]');
  }

  async goto() {
    await this.navigateTo('/pracownicy');
    await this.waitForPageLoad();
  }

  async openAddEmployeeForm() {
    await this.addEmployeeBtn.click();
    await this.page.waitForSelector('[data-testid="employee-name-input"]');
  }

  async createEmployee(name: string) {
    await this.openAddEmployeeForm();
    await this.employeeNameInput.fill(name);
    await this.saveEmployeeBtn.click();
    await this.waitForPageLoad();
  }

  async assignPosition(positionName: string) {
    const positionSelect = this.page.locator('select[name="position"], [data-testid*="position-select"]');
    await positionSelect.selectOption({ label: positionName });
  }

  async switchToShiftsTab() {
    await this.page.click('button:has-text("Grafik"), [role="tab"]:has-text("Grafik")');
    await this.waitForPageLoad();
  }

  async employeeExists(name: string): Promise<boolean> {
    return this.employeesTable.locator(`text=${name}`).isVisible();
  }
}
