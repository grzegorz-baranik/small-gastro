import client from './client'
import type {
  DateRangeRequest,
  DaySummaryResponse,
  MonthlyTrendsResponse,
  IngredientUsageResponse,
  SpoilageReportResponse,
} from '../types'

/**
 * Helper function to trigger file download from a Blob
 */
function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

/**
 * Get daily summary report for a specific day
 */
export async function getDailySummaryReport(recordId: number): Promise<DaySummaryResponse> {
  const { data } = await client.get<DaySummaryResponse>(`/daily-records/${recordId}/summary`)
  return data
}

/**
 * Export daily summary report to Excel
 */
export async function exportDailySummaryExcel(recordId: number, date: string): Promise<void> {
  const response = await client.get(`/reports/daily-summary/${recordId}/excel`, {
    responseType: 'blob',
  })
  downloadBlob(response.data, `raport-dzienny-${date}.xlsx`)
}

/**
 * Get monthly trends report for a date range
 */
export async function getMonthlyTrendsReport(range: DateRangeRequest): Promise<MonthlyTrendsResponse> {
  const { data } = await client.get<MonthlyTrendsResponse>('/reports/monthly-trends', {
    params: range,
  })
  return data
}

/**
 * Export monthly trends report to Excel
 */
export async function exportMonthlyTrendsExcel(range: DateRangeRequest): Promise<void> {
  const response = await client.get('/reports/monthly-trends/excel', {
    params: range,
    responseType: 'blob',
  })
  downloadBlob(response.data, `trendy-${range.start_date}-${range.end_date}.xlsx`)
}

/**
 * Get ingredient usage report for a date range
 */
export async function getIngredientUsageReport(
  range: DateRangeRequest,
  ingredientIds?: number[]
): Promise<IngredientUsageResponse> {
  const { data } = await client.get<IngredientUsageResponse>('/reports/ingredient-usage', {
    params: {
      ...range,
      ingredient_ids: ingredientIds?.join(',') || undefined,
    },
  })
  return data
}

/**
 * Export ingredient usage report to Excel
 */
export async function exportIngredientUsageExcel(
  range: DateRangeRequest,
  ingredientIds?: number[]
): Promise<void> {
  const response = await client.get('/reports/ingredient-usage/excel', {
    params: {
      ...range,
      ingredient_ids: ingredientIds?.join(',') || undefined,
    },
    responseType: 'blob',
  })
  downloadBlob(response.data, `zuzycie-skladnikow-${range.start_date}-${range.end_date}.xlsx`)
}

/**
 * Get spoilage report for a date range
 */
export async function getSpoilageReport(range: DateRangeRequest): Promise<SpoilageReportResponse> {
  const { data } = await client.get<SpoilageReportResponse>('/reports/spoilage', {
    params: range,
  })
  return data
}

/**
 * Export spoilage report to Excel
 */
export async function exportSpoilageExcel(range: DateRangeRequest): Promise<void> {
  const response = await client.get('/reports/spoilage/excel', {
    params: range,
    responseType: 'blob',
  })
  downloadBlob(response.data, `straty-${range.start_date}-${range.end_date}.xlsx`)
}
