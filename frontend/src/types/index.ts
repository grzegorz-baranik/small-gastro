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
  is_primary: boolean
  ingredient_name?: string
  ingredient_unit_type?: string
}

export interface ProductVariantInProduct {
  id: number
  name: string | null
  price_pln: number
  is_active: boolean
  ingredients: ProductIngredient[]
  created_at: string
}

export interface Product {
  id: number
  name: string
  has_variants: boolean
  is_active: boolean
  sort_order: number
  variants: ProductVariantInProduct[]
  created_at: string
  updated_at: string
}

export interface ProductReorderRequest {
  product_ids: number[]
}

export interface ProductReorderResponse {
  message: string
  updated_count: number
}

export interface ProductCreate {
  name: string
  price_pln: number
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

export interface LeafCategory {
  id: number
  name: string
  parent_id: number | null
  level: number
  is_active: boolean
  full_path: string  // e.g., "Koszty operacyjne > Skladniki > Warzywa"
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
export type WagePeriodType = 'daily' | 'weekly' | 'biweekly' | 'monthly'

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
  // Wage-specific fields
  employee_id: number | null
  employee_name: string | null
  wage_period_type: WagePeriodType | null
  wage_period_start: string | null
  wage_period_end: string | null
}

export interface TransactionCreate {
  type: TransactionType
  category_id?: number
  amount: number
  payment_method: PaymentMethod
  description?: string
  transaction_date: string
  daily_record_id?: number
  // Wage-specific fields
  employee_id?: number
  wage_period_type?: WagePeriodType
  wage_period_start?: string
  wage_period_end?: string
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
  name: string | null
  price_pln: number
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProductVariantCreate {
  name?: string | null
  price_pln: number
  is_default?: boolean
}

export interface ProductVariantUpdate {
  name?: string | null
  price_pln?: number
  is_default?: boolean
  is_active?: boolean
}

export interface ProductVariantListResponse {
  items: ProductVariantWithIngredients[]
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

// Mid-Day Operations types

// Delivery types (Multi-item structure)
export interface DeliveryItem {
  id: number
  delivery_id: number
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  quantity: number
  cost_pln: number | null
  created_at: string
}

export interface DeliveryItemCreate {
  ingredient_id: number
  quantity: number
  cost_pln?: number | null
  expiry_date?: string | null
}

export interface Delivery {
  id: number
  daily_record_id: number
  supplier_name: string | null
  invoice_number: string | null
  total_cost_pln: number
  notes: string | null
  transaction_id: number | null
  items: DeliveryItem[]
  delivered_at: string
  created_at: string
}

export interface DeliveryCreate {
  daily_record_id: number
  items: DeliveryItemCreate[]
  total_cost_pln: number
  destination?: 'storage' | 'shop'
  supplier_name?: string | null
  invoice_number?: string | null
  notes?: string | null
  delivered_at?: string
}

// Storage Transfer types
export interface StorageTransfer {
  id: number
  daily_record_id: number
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  quantity: number
  transferred_at: string
}

export interface StorageTransferCreate {
  daily_record_id: number
  ingredient_id: number
  quantity: number
}

// Transfer stock info for display in TransferModal
export interface TransferStockItem {
  ingredient_id: number
  ingredient_name: string
  unit_type: 'weight' | 'count'
  unit_label: string
  storage_quantity: number
  shop_quantity: number
}

// Spoilage types - must match backend SpoilageReason enum
export type SpoilageReason = 'expired' | 'over_prepared' | 'contaminated' | 'equipment_failure' | 'other'

export interface Spoilage {
  id: number
  daily_record_id: number
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  quantity: number
  reason: SpoilageReason
  notes: string | null
  recorded_at: string
}

export interface SpoilageCreate {
  daily_record_id: number
  ingredient_id: number
  quantity: number
  reason: SpoilageReason
  notes?: string
  batch_id?: number | null
}

// Summary types for day wizard (flattened single-ingredient items)
export interface DeliverySummaryItem {
  id: number
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  quantity: number
  price_pln: number
  delivered_at: string
}

export interface TransferSummaryItem {
  id: number
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  quantity: number
  transferred_at: string
}

export interface SpoilageSummaryItem {
  id: number
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  quantity: number
  reason: SpoilageReason
  notes: string | null
  recorded_at: string
}

// Report types

// Date range request for reports
export interface DateRangeRequest {
  start_date: string // YYYY-MM-DD
  end_date: string // YYYY-MM-DD
}

// Monthly trends report
export interface MonthlyTrendItem {
  date: string
  income_pln: number
  delivery_cost_pln: number
  spoilage_cost_pln: number
  profit_pln: number
}

export interface MonthlyTrendsResponse {
  items: MonthlyTrendItem[]
  total_income_pln: number
  total_costs_pln: number
  avg_daily_income_pln: number
  best_day: { date: string; income_pln: number } | null
  worst_day: { date: string; income_pln: number } | null
}

// Ingredient usage report
export interface IngredientUsageItem {
  date: string
  day_of_week: string
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  opening: number
  deliveries: number
  transfers: number
  spoilage: number
  closing: number
  usage: number
  discrepancy: number | null
  discrepancy_percent: number | null
}

export interface IngredientUsageSummaryItem {
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  total_used: number
  avg_daily_usage: number
  days_with_data: number
}

export interface IngredientUsageResponse {
  start_date: string
  end_date: string
  filtered_ingredient_ids: number[] | null
  items: IngredientUsageItem[]
  summary: IngredientUsageSummaryItem[]
}

// Spoilage report
export interface SpoilageReportItem {
  id: number
  date: string
  day_of_week: string
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  quantity: number
  reason: SpoilageReason
  reason_label: string
  notes: string | null
}

export interface SpoilageByReasonSummary {
  reason: SpoilageReason
  reason_label: string
  total_count: number
  total_quantity: number
}

export interface SpoilageByIngredientSummary {
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  total_count: number
  total_quantity: number
}

export interface SpoilageReportResponse {
  start_date: string
  end_date: string
  group_by: string
  items: SpoilageReportItem[]
  by_reason: SpoilageByReasonSummary[]
  by_ingredient: SpoilageByIngredientSummary[]
  total_count: number
}

// Stock Levels types (Inventory Page)
export interface StockLevel {
  ingredient_id: number
  ingredient_name: string
  unit_type: 'weight' | 'count'
  unit_label: string
  warehouse_qty: number
  shop_qty: number
  total_qty: number
  batches_count: number
  nearest_expiry: string | null
}

// Stock Adjustment types
export type AdjustmentType = 'set' | 'add' | 'subtract'

export interface StockAdjustmentCreate {
  ingredient_id: number
  location: 'storage' | 'shop'
  adjustment_type: AdjustmentType
  quantity: number
  reason: string
  notes?: string
}

export interface StockAdjustmentResponse {
  id: number
  ingredient_id: number
  ingredient_name: string
  location: string
  adjustment_type: string
  previous_quantity: number
  new_quantity: number
  adjustment_amount: number
  reason: string
  notes?: string
  created_at: string
}

// Delivery destination type
export type DeliveryDestination = 'storage' | 'shop'

// Batch tracking types
export interface IngredientBatch {
  id: number
  batch_number: string
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  delivery_item_id: number | null
  expiry_date: string | null
  initial_quantity: number
  remaining_quantity: number
  location: 'storage' | 'shop'
  is_active: boolean
  days_until_expiry: number | null
  is_expiring_soon: boolean
  age_days: number
  notes: string | null
  created_at: string
}

export interface ExpiryAlert {
  batch_id: number
  batch_number: string
  ingredient_id: number
  ingredient_name: string
  expiry_date: string
  days_until_expiry: number
  remaining_quantity: number
  unit_label: string
  location: string
  alert_level: 'warning' | 'critical' | 'expired'
}

export interface ExpiryAlertsResponse {
  alerts: ExpiryAlert[]
  expired_count: number
  critical_count: number
  warning_count: number
}

export interface BatchInventoryItem {
  batch_id: number
  batch_number: string
  expiry_date: string | null
  remaining_quantity: number
  age_days: number
  is_expiring_soon: boolean
  fifo_order: number
}

export interface IngredientBatchSummary {
  ingredient_id: number
  ingredient_name: string
  unit_label: string
  total_quantity: number
  batch_count: number
  oldest_batch_age_days: number
  nearest_expiry_date: string | null
  nearest_expiry_days: number | null
  batches: BatchInventoryItem[]
}

// Recorded Sales types (hybrid sales tracking)
export type VoidReason = 'mistake' | 'customer_refund' | 'duplicate' | 'other'

export interface RecordedSaleCreate {
  product_variant_id: number
  quantity?: number // defaults to 1
}

export interface RecordedSaleVoid {
  reason: VoidReason
  notes?: string
}

export interface RecordedSale {
  id: number
  daily_record_id: number
  product_variant_id: number
  product_name: string
  variant_name: string | null
  shift_assignment_id: number | null
  quantity: number
  unit_price_pln: number
  total_pln: number
  recorded_at: string
  voided_at: string | null
  void_reason: string | null
  void_notes: string | null
}

export interface DaySalesTotal {
  total_pln: number
  sales_count: number
  items_count: number
}

// Sales Reconciliation types
export interface ProductReconciliation {
  product_variant_id: number
  product_name: string
  variant_name: string | null
  recorded_qty: number
  recorded_revenue: number
  calculated_qty: number
  calculated_revenue: number
  qty_difference: number
  revenue_difference: number
}

export interface MissingSuggestion {
  product_variant_id: number
  product_name: string
  variant_name: string | null
  suggested_qty: number
  suggested_revenue: number
  reason: string
}

export interface ReconciliationReport {
  daily_record_id: number
  recorded_total_pln: number
  calculated_total_pln: number
  discrepancy_pln: number
  discrepancy_percent: number
  has_critical_discrepancy: boolean
  has_no_recorded_sales: boolean
  by_product: ProductReconciliation[]
  suggestions: MissingSuggestion[]
}

// Product Category types (for sales UI)
export interface ProductCategory {
  id: number
  name: string
  sort_order: number
}

// Products for sales entry UI
export interface ProductVariantForSale {
  id: number
  product_id: number
  name: string | null
  price_pln: number
  is_default: boolean
  today_sold_count: number
}

export interface ProductForSale {
  id: number
  name: string
  category_id: number | null
  category_name: string | null
  variants: ProductVariantForSale[]
}

// Re-export employee/shift management types
export * from './positions'
export * from './employees'
export * from './shift_assignments'
export * from './wage_analytics'
