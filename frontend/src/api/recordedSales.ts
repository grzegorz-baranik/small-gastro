import client from './client'
import type {
  RecordedSale,
  RecordedSaleCreate,
  RecordedSaleVoid,
  DaySalesTotal,
  ReconciliationReport,
  ProductCategory,
  ProductForSale,
} from '../types'

// -----------------------------------------------------------------------------
// Sales Recording
// -----------------------------------------------------------------------------

/**
 * Record a new sale for a daily record.
 * Requires an open day.
 */
export async function recordSale(
  dailyRecordId: number,
  data: RecordedSaleCreate
): Promise<RecordedSale> {
  const { data: response } = await client.post<RecordedSale>(
    `/daily-records/${dailyRecordId}/sales`,
    data
  )
  return response
}

/**
 * Get all recorded sales for a daily record.
 * @param dailyRecordId - The ID of the daily record
 * @param includeVoided - If true, includes voided sales in the response
 */
export async function getDaySales(
  dailyRecordId: number,
  includeVoided: boolean = false
): Promise<RecordedSale[]> {
  const { data } = await client.get<RecordedSale[]>(
    `/daily-records/${dailyRecordId}/sales`,
    {
      params: { include_voided: includeVoided },
    }
  )
  return data
}

/**
 * Get the total sales summary for a daily record.
 * Returns total PLN, sales count, and items count.
 */
export async function getDayTotal(dailyRecordId: number): Promise<DaySalesTotal> {
  const { data } = await client.get<DaySalesTotal>(
    `/daily-records/${dailyRecordId}/sales/total`
  )
  return data
}

/**
 * Void (soft delete) a recorded sale.
 * Requires the day to be open and the sale to not be already voided.
 */
export async function voidSale(
  dailyRecordId: number,
  saleId: number,
  data: RecordedSaleVoid
): Promise<RecordedSale> {
  const { data: response } = await client.post<RecordedSale>(
    `/daily-records/${dailyRecordId}/sales/${saleId}/void`,
    data
  )
  return response
}

// -----------------------------------------------------------------------------
// Reconciliation
// -----------------------------------------------------------------------------

/**
 * Get the reconciliation report comparing recorded vs calculated sales.
 * Shows discrepancies between manually recorded sales and inventory-based calculations.
 */
export async function getReconciliation(
  dailyRecordId: number
): Promise<ReconciliationReport> {
  const { data } = await client.get<ReconciliationReport>(
    `/daily-records/${dailyRecordId}/reconciliation`
  )
  return data
}

// -----------------------------------------------------------------------------
// Product Categories
// -----------------------------------------------------------------------------

/**
 * Get product categories for the sales UI.
 * Categories are used to group products (e.g., "Kebaby", "Burgery", "Napoje").
 */
export async function getCategories(): Promise<ProductCategory[]> {
  const { data } = await client.get<ProductCategory[]>('/products/categories')
  return data
}

/**
 * Get products with variants for sales entry.
 * Includes today's sold count per variant for display on buttons.
 */
export async function getProductsForSale(dailyRecordId: number): Promise<ProductForSale[]> {
  const { data } = await client.get<ProductForSale[]>(
    `/daily-records/${dailyRecordId}/sales/products`
  )
  return data
}

/**
 * Get recent sales for display in the recent sales list.
 */
export async function getRecentSales(
  dailyRecordId: number,
  limit: number = 10
): Promise<RecordedSale[]> {
  const { data } = await client.get<RecordedSale[]>(
    `/daily-records/${dailyRecordId}/sales/recent`,
    { params: { limit } }
  )
  return data
}
