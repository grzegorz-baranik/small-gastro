import client from './client'
import type { WageAnalyticsResponse, HoursCalculationResponse } from '../types'

export interface WageAnalyticsParams {
  month: number
  year: number
  employee_id?: number
}

export async function getWageAnalytics(params: WageAnalyticsParams): Promise<WageAnalyticsResponse> {
  const { data } = await client.get('/analytics/wages', { params })
  return data
}

export async function calculateHoursForPeriod(
  employeeId: number,
  startDate: string,
  endDate: string
): Promise<HoursCalculationResponse> {
  const { data } = await client.get(`/employees/${employeeId}/hours`, {
    params: {
      start_date: startDate,
      end_date: endDate
    }
  })
  return data
}
