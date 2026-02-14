import { useMemo } from 'react'
import type { UsageItem, DiscrepancyAlert } from '../types'

export type { DiscrepancyAlert }

export interface CalculatedRow {
  ingredientId: number
  ingredientName: string
  unitType: 'weight' | 'count'
  unitLabel: string
  opening: number
  deliveries: number
  transfers: number
  spoilage: number
  expected: number
  closing: number | null
  usage: number | null
  expectedUsage: number | null
  discrepancyPercent: number | null
  discrepancyLevel: 'ok' | 'warning' | 'critical' | null
}

interface UseClosingCalculationsProps {
  usageItems: UsageItem[]
  closingInventory: Record<number, string>
}

interface CalculationResult {
  rows: CalculatedRow[]
  alerts: DiscrepancyAlert[]
  isValid: boolean
}

export function useClosingCalculations({
  usageItems,
  closingInventory,
}: UseClosingCalculationsProps): CalculationResult {
  return useMemo(() => {
    const rows: CalculatedRow[] = []
    const alerts: DiscrepancyAlert[] = []
    let isValid = true

    for (const item of usageItems) {
      const closingValue = closingInventory[item.ingredient_id]
      const closing = closingValue !== undefined && closingValue !== ''
        ? parseFloat(closingValue)
        : null

      let usage: number | null = null
      let discrepancyPercent: number | null = null
      let discrepancyLevel: 'ok' | 'warning' | 'critical' | null = null

      if (closing !== null && !isNaN(closing)) {
        // Calculate usage: Expected - Closing
        usage = item.expected_closing - closing

        // Calculate discrepancy (compare actual usage vs expected usage)
        const expectedUsage = item.expected_usage
        if (expectedUsage !== null && expectedUsage !== undefined && expectedUsage > 0) {
          const diff = Math.abs(usage - expectedUsage)
          discrepancyPercent = (diff / expectedUsage) * 100

          if (discrepancyPercent <= 5) {
            discrepancyLevel = 'ok'
          } else if (discrepancyPercent <= 10) {
            discrepancyLevel = 'warning'
            alerts.push({
              ingredient_id: item.ingredient_id,
              ingredient_name: item.ingredient_name,
              discrepancy_percent: discrepancyPercent,
              level: 'warning',
              message: `${item.ingredient_name}: ${discrepancyPercent.toFixed(1)}%`,
            })
          } else {
            discrepancyLevel = 'critical'
            alerts.push({
              ingredient_id: item.ingredient_id,
              ingredient_name: item.ingredient_name,
              discrepancy_percent: discrepancyPercent,
              level: 'critical',
              message: `${item.ingredient_name}: ${discrepancyPercent.toFixed(1)}%`,
            })
          }
        } else if (expectedUsage === 0 && usage === 0) {
          // No expected usage and no actual usage - that's OK
          discrepancyLevel = 'ok'
          discrepancyPercent = 0
        } else if (expectedUsage === 0 && usage !== 0) {
          // No expected usage but there was actual usage - mark as critical
          discrepancyLevel = 'critical'
          discrepancyPercent = 100
          alerts.push({
            ingredient_id: item.ingredient_id,
            ingredient_name: item.ingredient_name,
            discrepancy_percent: 100,
            level: 'critical',
            message: `${item.ingredient_name}: N/A`,
          })
        }
      } else if (closingValue === '' || closingValue === undefined) {
        isValid = false
      }

      rows.push({
        ingredientId: item.ingredient_id,
        ingredientName: item.ingredient_name,
        unitType: item.unit_type as 'weight' | 'count',
        unitLabel: item.unit_label,
        opening: item.opening_quantity,
        deliveries: item.deliveries_quantity,
        transfers: item.transfers_quantity,
        spoilage: item.spoilage_quantity,
        expected: item.expected_closing,
        closing,
        usage,
        expectedUsage: item.expected_usage,
        discrepancyPercent,
        discrepancyLevel,
      })
    }

    return { rows, alerts, isValid }
  }, [usageItems, closingInventory])
}
