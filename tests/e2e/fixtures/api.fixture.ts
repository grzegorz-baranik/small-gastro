import { test as base, APIRequestContext, expect } from '@playwright/test';

/**
 * API Helper for test data seeding.
 * Uses backend API to create test fixtures before UI tests.
 */
export class ApiHelper {
  private baseURL: string;

  constructor(private request: APIRequestContext) {
    // Backend API URL (port 8303 for feature-day-closing branch)
    this.baseURL = 'http://localhost:8303/api/v1';
  }

  // ==================== Ingredients ====================

  async createIngredient(data: {
    name: string;
    unit_type: 'weight' | 'count';
    unit_label?: string;
  }) {
    const response = await this.request.post(`${this.baseURL}/ingredients`, {
      data: {
        name: data.name,
        unit_type: data.unit_type,
        unit_label: data.unit_label || (data.unit_type === 'weight' ? 'kg' : 'szt'),
        is_active: true,
      },
    });
    expect(response.ok(), `Failed to create ingredient: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  async getIngredients() {
    const response = await this.request.get(`${this.baseURL}/ingredients`);
    return response.json();
  }

  // ==================== Products ====================

  async createProduct(data: {
    name: string;
    price_pln: number;
    ingredients?: Array<{ ingredient_id: number; quantity: number; is_primary?: boolean }>;
  }) {
    const response = await this.request.post(`${this.baseURL}/products/simple`, {
      data: {
        name: data.name,
        price_pln: data.price_pln,
        ingredients: data.ingredients || [],
      },
    });
    expect(response.ok(), `Failed to create product: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  async getProducts() {
    const response = await this.request.get(`${this.baseURL}/products`);
    return response.json();
  }

  // ==================== Positions ====================

  async createPosition(data: { name: string; hourly_rate: number }) {
    const response = await this.request.post(`${this.baseURL}/positions`, {
      data: {
        name: data.name,
        hourly_rate: data.hourly_rate.toString(),
      },
    });
    expect(response.ok(), `Failed to create position: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  // ==================== Employees ====================

  async createEmployee(data: {
    name: string;
    position_id?: number;
    hourly_rate?: number;
  }) {
    const response = await this.request.post(`${this.baseURL}/employees`, {
      data: {
        name: data.name,
        position_id: data.position_id,
        hourly_rate: data.hourly_rate?.toString(),
        is_active: true,
      },
    });
    expect(response.ok(), `Failed to create employee: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  // ==================== Categories ====================

  async createCategory(data: { name: string; parent_id?: number }) {
    const response = await this.request.post(`${this.baseURL}/categories`, {
      data: {
        name: data.name,
        parent_id: data.parent_id || null,
      },
    });
    expect(response.ok(), `Failed to create category: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  // ==================== Daily Records ====================

  async openDay(data: {
    date: string;
    opening_inventory: Array<{ ingredient_id: number; quantity: string }>;
    notes?: string;
  }) {
    const response = await this.request.post(`${this.baseURL}/daily-records/open?force=true`, {
      data: {
        date: data.date,
        opening_inventory: data.opening_inventory,
        notes: data.notes || '',
      },
    });
    expect(response.ok(), `Failed to open day: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  async getOpenDay() {
    const response = await this.request.get(`${this.baseURL}/daily-records/status/open`);
    if (response.status() === 404) return null;
    return response.json();
  }

  async getTodayRecord() {
    const response = await this.request.get(`${this.baseURL}/daily-records/today`);
    if (response.status() === 404) return null;
    const data = await response.json();
    // The endpoint returns null if no record exists
    return data;
  }

  async deleteDay(recordId: number) {
    const response = await this.request.delete(`${this.baseURL}/daily-records/${recordId}`);
    // 204 = success, 404 = already deleted
    return response.status() === 204 || response.status() === 404;
  }

  async ensureDayDeleted() {
    // First try to get today's record
    const todayRecord = await this.getTodayRecord();
    if (todayRecord && todayRecord.id) {
      await this.deleteDay(todayRecord.id);
    }
    // Also check for any open day
    const openDay = await this.getOpenDay();
    if (openDay && openDay.id) {
      await this.deleteDay(openDay.id);
    }
  }

  async closeDay(recordId: number, data: {
    closing_inventory: Array<{ ingredient_id: number; quantity: string }>;
    notes?: string;
  }) {
    const response = await this.request.post(`${this.baseURL}/daily-records/${recordId}/close`, {
      data: {
        closing_inventory: data.closing_inventory,
        notes: data.notes || '',
      },
    });
    expect(response.ok(), `Failed to close day: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  // ==================== Transactions ====================

  async createExpense(data: {
    category_id: number;
    amount: number;
    description?: string;
    daily_record_id?: number;
    payment_method?: 'cash' | 'card' | 'bank_transfer';
    transaction_date?: string;
  }) {
    const response = await this.request.post(`${this.baseURL}/transactions`, {
      data: {
        type: 'expense',
        category_id: data.category_id,
        amount: data.amount.toString(),
        payment_method: data.payment_method || 'cash',
        description: data.description || '',
        transaction_date: data.transaction_date || new Date().toISOString().split('T')[0],
        daily_record_id: data.daily_record_id,
      },
    });
    expect(response.ok(), `Failed to create expense: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  // ==================== Shift Templates ====================

  async createShiftTemplate(data: {
    employee_id: number;
    day_of_week: number; // 0=Monday, 6=Sunday
    start_time: string;
    end_time: string;
  }) {
    const response = await this.request.post(`${this.baseURL}/shift-templates`, {
      data: {
        employee_id: data.employee_id,
        day_of_week: data.day_of_week,
        start_time: data.start_time,
        end_time: data.end_time,
      },
    });
    expect(response.ok(), `Failed to create shift template: ${await response.text()}`).toBeTruthy();
    return response.json();
  }

  // ==================== Cleanup ====================

  async deleteAllIngredients() {
    const ingredients = await this.getIngredients();
    for (const ing of ingredients.items || []) {
      await this.request.delete(`${this.baseURL}/ingredients/${ing.id}`);
    }
  }

  async deleteAllProducts() {
    const products = await this.getProducts();
    for (const prod of products.items || []) {
      await this.request.delete(`${this.baseURL}/products/${prod.id}`);
    }
  }
}

/**
 * Extended test fixture with API helper.
 */
export const test = base.extend<{ api: ApiHelper }>({
  api: async ({ request }, use) => {
    const api = new ApiHelper(request);
    await use(api);
  },
});

export { expect } from '@playwright/test';
