import client from './client'
import type { SalesItem, SalesItemCreate, DailySalesSummary } from '../types'

export async function getTodaySales(): Promise<DailySalesSummary | null> {
  try {
    const { data } = await client.get('/sales/today')
    return data
  } catch (error: unknown) {
    if ((error as { response?: { status?: number } }).response?.status === 404) {
      return null
    }
    throw error
  }
}

export async function getSalesForDay(dailyRecordId: number): Promise<DailySalesSummary> {
  const { data } = await client.get(`/sales/daily-record/${dailyRecordId}`)
  return data
}

export async function createSale(sale: SalesItemCreate): Promise<SalesItem> {
  const { data } = await client.post('/sales', sale)
  return data
}

export async function deleteSale(saleId: number): Promise<void> {
  await client.delete(`/sales/${saleId}`)
}
