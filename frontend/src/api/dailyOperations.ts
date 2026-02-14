import client from './client'
import type {
  DailyRecord,
  OpenDayRequest,
  CloseDayRequest,
  PreviousClosingResponse,
  DaySummaryResponse,
  RecentDayRecord,
  InventorySnapshotItem,
  DayEventsSummary,
} from '../types'

/**
 * Get today's daily record
 * Returns null if no record exists for today
 */
export async function getTodayRecord(): Promise<DailyRecord | null> {
  try {
    const { data } = await client.get<DailyRecord>('/daily-records/today')
    return data
  } catch (error: unknown) {
    if ((error as { response?: { status?: number } }).response?.status === 404) {
      return null
    }
    throw error
  }
}

/**
 * Get the currently open day (any date)
 * Returns null if no day is currently open
 */
export async function getOpenRecord(): Promise<DailyRecord | null> {
  try {
    const { data } = await client.get<DailyRecord>('/daily-records/status/open')
    return data
  } catch (error: unknown) {
    if ((error as { response?: { status?: number } }).response?.status === 404) {
      return null
    }
    throw error
  }
}

/**
 * Get the last closing inventory to pre-fill opening values
 */
export async function getPreviousClosing(): Promise<PreviousClosingResponse> {
  const { data } = await client.get<PreviousClosingResponse>('/daily-records/previous-closing')
  return data
}

/**
 * Open a new day with opening inventory counts
 */
export async function openDay(request: OpenDayRequest): Promise<DailyRecord> {
  const { data } = await client.post<DailyRecord>('/daily-records/open', request)
  return data
}

/**
 * Close the current day with closing inventory counts
 */
export async function closeDay(
  recordId: number,
  closingInventory: InventorySnapshotItem[],
  notes?: string
): Promise<DailyRecord> {
  const request: CloseDayRequest = {
    closing_inventory: closingInventory,
    notes,
  }
  const { data } = await client.post<DailyRecord>(`/daily-records/${recordId}/close`, request)
  return data
}

/**
 * Get detailed summary for a specific day
 */
export async function getDaySummary(recordId: number): Promise<DaySummaryResponse> {
  const { data } = await client.get<DaySummaryResponse>(`/daily-records/${recordId}/summary`)
  return data
}

/**
 * Get recent day records for history display
 */
export async function getRecentDays(limit: number = 7): Promise<RecentDayRecord[]> {
  const { data } = await client.get<RecentDayRecord[]>('/daily-records/recent', {
    params: { limit },
  })
  return data
}

/**
 * Get day events summary (deliveries, transfers, spoilage) for a specific day
 */
export async function getDayEvents(recordId: number): Promise<DayEventsSummary> {
  const { data } = await client.get<DayEventsSummary>(`/daily-records/${recordId}/events`)
  return data
}

/**
 * Get all daily records with optional filtering
 */
export async function getDailyRecords(params?: {
  skip?: number
  limit?: number
  status?: 'open' | 'closed'
}): Promise<{ items: DailyRecord[]; total: number }> {
  const { data } = await client.get<{ items: DailyRecord[]; total: number }>('/daily-records/', {
    params,
  })
  return data
}

/**
 * Get a specific daily record by ID
 */
export async function getDailyRecord(recordId: number): Promise<DailyRecord> {
  const { data } = await client.get<DailyRecord>(`/daily-records/${recordId}`)
  return data
}

/**
 * Check if previous day needs to be closed
 */
export async function checkPreviousDayStatus(): Promise<{
  needs_closing: boolean
  previous_date: string | null
  previous_record_id: number | null
}> {
  const { data } = await client.get<{
    needs_closing: boolean
    previous_date: string | null
    previous_record_id: number | null
  }>('/daily-records/check-previous')
  return data
}
