import client from './client'
import type { DailyRecord, DailyRecordCreate, InventorySnapshotCreate } from '../types'

export async function getDailyRecords(): Promise<DailyRecord[]> {
  const { data } = await client.get('/daily-records/')
  return data
}

export async function getTodayRecord(): Promise<DailyRecord | null> {
  try {
    const { data } = await client.get('/daily-records/today')
    return data
  } catch (error: unknown) {
    if ((error as { response?: { status?: number } }).response?.status === 404) {
      return null
    }
    throw error
  }
}

export async function openDay(data: DailyRecordCreate): Promise<DailyRecord> {
  const { data: result } = await client.post('/daily-records/open', data)
  return result
}

export async function closeDay(recordId: number, closingInventory: InventorySnapshotCreate[], notes?: string): Promise<DailyRecord> {
  const { data } = await client.post(`/daily-records/${recordId}/close`, {
    notes,
    closing_inventory: closingInventory,
  })
  return data
}

export async function getDailySummary(recordId: number) {
  const { data } = await client.get(`/daily-records/${recordId}/summary`)
  return data
}
