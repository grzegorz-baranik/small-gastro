// Re-export from dailyOperations for backwards compatibility
// This file is deprecated, use dailyOperations.ts instead

export {
  getTodayRecord,
  openDay,
  closeDay,
  getDaySummary,
  getDailyRecords,
  getDailyRecord,
  getRecentDays,
  getPreviousClosing,
  getDayEvents,
  checkPreviousDayStatus,
} from './dailyOperations'

// Legacy exports with old signatures for compatibility
import client from './client'
import type { DailyRecord, DailyRecordCreate, InventorySnapshotCreate } from '../types'

/**
 * @deprecated Use openDay from dailyOperations.ts instead
 */
export async function openDayLegacy(data: DailyRecordCreate): Promise<DailyRecord> {
  const { data: result } = await client.post('/daily-records/open', data)
  return result
}

/**
 * @deprecated Use closeDay from dailyOperations.ts instead
 */
export async function closeDayLegacy(
  recordId: number,
  closingInventory: InventorySnapshotCreate[],
  notes?: string
): Promise<DailyRecord> {
  const { data } = await client.post(`/daily-records/${recordId}/close`, {
    notes,
    closing_inventory: closingInventory,
  })
  return data
}
