import client from './client'
import type { DashboardOverview, DiscrepancyWarning } from '../types'

export async function getDashboardOverview(): Promise<DashboardOverview> {
  const { data } = await client.get('/dashboard/overview')
  return data
}

export async function getIncomeBreakdown(period: 'today' | 'week' | 'month') {
  const { data } = await client.get('/dashboard/income', { params: { period } })
  return data
}

export async function getExpensesBreakdown(period: 'today' | 'week' | 'month') {
  const { data } = await client.get('/dashboard/expenses', { params: { period } })
  return data
}

export async function getProfitData(period: 'today' | 'week' | 'month') {
  const { data } = await client.get('/dashboard/profit', { params: { period } })
  return data
}

export async function getDiscrepancyWarnings(daysBack = 7): Promise<DiscrepancyWarning[]> {
  const { data } = await client.get('/dashboard/warnings', { params: { days_back: daysBack } })
  return data
}
