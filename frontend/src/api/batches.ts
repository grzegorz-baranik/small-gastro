import client from './client'
import type { IngredientBatch, ExpiryAlertsResponse, IngredientBatchSummary } from '../types'

export async function getExpiryAlerts(daysAhead: number = 7): Promise<ExpiryAlertsResponse> {
  const { data } = await client.get<ExpiryAlertsResponse>('/batches/expiry-alerts', {
    params: { days_ahead: daysAhead },
  })
  return data
}

export async function getBatchesForIngredient(
  ingredientId: number,
  location?: 'storage' | 'shop',
  activeOnly: boolean = true
): Promise<IngredientBatch[]> {
  const { data } = await client.get<IngredientBatch[]>(`/batches/ingredient/${ingredientId}`, {
    params: { location, active_only: activeOnly },
  })
  return data
}

export async function getIngredientBatchSummary(
  ingredientId: number,
  location?: 'storage' | 'shop'
): Promise<IngredientBatchSummary> {
  const { data } = await client.get<IngredientBatchSummary>(
    `/batches/ingredient/${ingredientId}/summary`,
    { params: { location } }
  )
  return data
}
