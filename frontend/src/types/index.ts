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
  total_income_pln: number | null
  total_delivery_cost_pln: number | null
  total_spoilage_cost_pln: number | null
  created_at: string
  updated_at: string | null
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

export interface OpenDayRequest {
  date: string
  notes?: string
  opening_inventory: InventorySnapshotItem[]
}

export interface CloseDayRequest {
  notes?: string
  closing_inventory: InventorySnapshotItem[]
}

// Inventory snapshot item for API requests
export interface InventorySnapshotItem {
  ingredient_id: number
  quantity: number
}

// Previous closing inventory response
export interface PreviousClosingItem {
  ingredient_id: number
  ingredient_name: string
  unit_type: UnitType
  unit_label: string
  quantity: number
}

export interface PreviousClosingResponse {
  date: string | null
  items: PreviousClosingItem[]
}

// Day events summary
export interface DayEventsSummary {
  deliveries_count: number
  deliveries_total_pln: number
  transfers_count: number
  spoilage_count: number
}

// Usage calculation item
export interface UsageItem {
  ingredient_id: number
  ingredient_name: string
  unit_type: UnitType
  unit_label: string
  opening_quantity: number
  deliveries_quantity: number
  transfers_quantity: number
  spoilage_quantity: number
  expected_closing: number
  closing_quantity: number | null
  usage: number | null
  expected_usage: number | null
  discrepancy: number | null
  discrepancy_percent: number | null
  discrepancy_level: 'ok' | 'warning' | 'critical' | null
}

// Day summary response
export interface DaySummaryResponse {
  daily_record: DailyRecord
  opening_time: string | null
  closing_time: string | null
  events: DayEventsSummary
  usage_items: UsageItem[]
  calculated_sales: CalculatedSaleItem[]
  total_income_pln: number
  discrepancy_alerts: DiscrepancyAlert[]
}

// Calculated sale item
export interface CalculatedSaleItem {
  product_id: number
  product_name: string
  variant_id: number | null
  variant_name: string | null
  quantity_sold: number
  unit_price_pln: number
  revenue_pln: number
}

// Discrepancy alert
export interface DiscrepancyAlert {
  ingredient_id: number
  ingredient_name: string
  discrepancy_percent: number
  level: 'ok' | 'warning' | 'critical'
  message: string
}

// Recent day record for history
export interface RecentDayRecord {
  id: number
  date: string
  status: DayStatus
  total_income_pln: number | null
  alerts_count: number
  opened_at: string | null
  closed_at: string | null
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
