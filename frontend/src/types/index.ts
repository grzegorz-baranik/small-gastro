// Ingredient types
export type UnitType = 'weight' | 'count'

export interface Ingredient {
  id: number
  name: string
  unit_type: UnitType
  current_stock_grams: number
  current_stock_count: number
  created_at: string
  updated_at: string
}

export interface IngredientCreate {
  name: string
  unit_type: UnitType
  current_stock_grams?: number
  current_stock_count?: number
}

// Product types
export interface ProductIngredient {
  id: number
  ingredient_id: number
  quantity: number
  ingredient_name?: string
  ingredient_unit_type?: string
}

export interface Product {
  id: number
  name: string
  price: number
  is_active: boolean
  ingredients: ProductIngredient[]
  created_at: string
  updated_at: string
}

export interface ProductCreate {
  name: string
  price: number
  ingredients?: { ingredient_id: number; quantity: number }[]
}

// Expense category types
export interface ExpenseCategory {
  id: number
  name: string
  parent_id: number | null
  level: number
  is_active: boolean
  children?: ExpenseCategory[]
}

// Daily record types
export type DayStatus = 'open' | 'closed'

export interface DailyRecord {
  id: number
  date: string
  status: DayStatus
  opened_at: string
  closed_at: string | null
  notes: string | null
  created_at: string
}

export interface InventorySnapshotCreate {
  ingredient_id: number
  quantity_grams?: number
  quantity_count?: number
}

export interface DailyRecordCreate {
  date: string
  notes?: string
  opening_inventory: InventorySnapshotCreate[]
}

// Inventory types
export interface InventorySnapshot {
  id: number
  daily_record_id: number
  ingredient_id: number
  ingredient_name?: string
  snapshot_type: 'open' | 'close'
  quantity_grams?: number
  quantity_count?: number
  recorded_at: string
}

export interface InventoryDiscrepancy {
  ingredient_id: number
  ingredient_name: string
  unit_type: string
  opening_quantity: number
  closing_quantity: number
  actual_used: number
  expected_used: number
  discrepancy: number
  discrepancy_percent: number | null
}

// Sales types
export interface SalesItem {
  id: number
  daily_record_id: number
  product_id: number
  product_name?: string
  quantity_sold: number
  unit_price: number
  total_price: number
  created_at: string
}

export interface SalesItemCreate {
  product_id: number
  quantity_sold: number
}

export interface DailySalesSummary {
  daily_record_id: number
  date: string
  items: SalesItem[]
  total_items_sold: number
  total_revenue: number
}

// Transaction types
export type TransactionType = 'expense' | 'revenue'
export type PaymentMethod = 'cash' | 'card' | 'bank_transfer'

export interface Transaction {
  id: number
  type: TransactionType
  category_id: number | null
  amount: number
  payment_method: PaymentMethod
  description: string | null
  transaction_date: string
  daily_record_id: number | null
  category_name: string | null
  created_at: string
}

export interface TransactionCreate {
  type: TransactionType
  category_id?: number
  amount: number
  payment_method: PaymentMethod
  description?: string
  transaction_date: string
  daily_record_id?: number
}

// Dashboard types
export interface DashboardOverview {
  today_revenue: number
  today_expenses: number
  today_profit: number
  week_revenue: number
  week_expenses: number
  week_profit: number
  month_revenue: number
  month_expenses: number
  month_profit: number
  day_is_open: boolean
  active_warnings: number
}

export interface DiscrepancyWarning {
  id: number
  date: string
  ingredient_id: number
  ingredient_name: string
  expected_used: number
  actual_used: number
  discrepancy: number
  discrepancy_percent: number
  severity: 'low' | 'medium' | 'high'
}

// Product Variant types
export interface ProductVariant {
  id: number
  product_id: number
  name: string
  price: number
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProductVariantCreate {
  name: string
  price: number
  is_default?: boolean
}

export interface ProductVariantUpdate {
  name?: string
  price?: number
  is_default?: boolean
  is_active?: boolean
}

export interface ProductVariantListResponse {
  items: ProductVariant[]
  total: number
}

// Variant Ingredient (Recipe) types
export interface VariantIngredient {
  id: number
  ingredient_id: number
  quantity: number
  is_primary: boolean
  ingredient_name?: string
  ingredient_unit_type?: string
  ingredient_unit_label?: string
}

export interface VariantIngredientCreate {
  ingredient_id: number
  quantity: number
  is_primary?: boolean
}

export interface VariantIngredientUpdate {
  quantity?: number
  is_primary?: boolean
}

export interface VariantIngredientListResponse {
  items: VariantIngredient[]
  total: number
}

// Extended variant with ingredients
export interface ProductVariantWithIngredients extends ProductVariant {
  ingredients: VariantIngredient[]
}
