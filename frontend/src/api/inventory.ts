import client from './client'
import type { StockLevel, StockAdjustmentCreate, StockAdjustmentResponse } from '../types'

// Get real-time stock levels for all ingredients
export async function getStockLevels(): Promise<StockLevel[]> {
  const { data } = await client.get<StockLevel[]>('/inventory/stock-levels')
  return data
}

// Create a stock adjustment
export async function createStockAdjustment(
  adjustment: StockAdjustmentCreate
): Promise<StockAdjustmentResponse> {
  const { data } = await client.post<StockAdjustmentResponse>('/inventory/adjustment', adjustment)
  return data
}
