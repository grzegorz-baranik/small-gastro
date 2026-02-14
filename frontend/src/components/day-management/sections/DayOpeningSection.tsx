import { useState, useEffect, useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  Copy,
  Save,
  AlertCircle,
  ArrowRight,
  Package,
} from 'lucide-react'
import LoadingSpinner from '../../common/LoadingSpinner'
import { useToast } from '../../../context/ToastContext'
import { getIngredients } from '../../../api/ingredients'
import { getDaySummary, getPreviousClosing } from '../../../api/dailyOperations'
import { formatQuantity } from '../../../utils/formatters'
import type { Ingredient, PreviousClosingItem, UsageItem } from '../../../types'

interface DayOpeningSectionProps {
  dayId: number
  isEditable: boolean
}

// API function for updating opening inventory (if needed)
// This would need to be implemented in the backend
async function updateOpeningInventory(
  _dayId: number,
  _inventory: { ingredient_id: number; quantity: number }[]
): Promise<void> {
  // TODO: Implement API call when backend endpoint is ready
  // For now, this is a placeholder
  throw new Error('Update opening inventory not implemented yet')
}

export default function DayOpeningSection({ dayId, isEditable }: DayOpeningSectionProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  // Local state for editable inventory
  const [inventory, setInventory] = useState<Record<number, string>>({})
  const [isDirty, setIsDirty] = useState(false)
  const [errors, setErrors] = useState<Record<number, string>>({})

  // Fetch day summary to get opening inventory
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({
    queryKey: ['daySummary', dayId],
    queryFn: () => getDaySummary(dayId),
    enabled: !!dayId,
  })

  // Fetch ingredients list
  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
    enabled: !!dayId,
  })

  // Fetch previous closing for comparison
  const { data: previousClosing } = useQuery({
    queryKey: ['previousClosing'],
    queryFn: getPreviousClosing,
    enabled: !!dayId,
  })

  // Create map of previous closing values
  const previousClosingMap = useMemo(() => {
    const map: Record<number, PreviousClosingItem> = {}
    if (previousClosing?.items) {
      previousClosing.items.forEach((item) => {
        map[item.ingredient_id] = item
      })
    }
    return map
  }, [previousClosing])

  // Create map of opening values from summary
  const openingValuesMap = useMemo(() => {
    const map: Record<number, UsageItem> = {}
    if (summary?.usage_items) {
      summary.usage_items.forEach((item) => {
        map[item.ingredient_id] = item
      })
    }
    return map
  }, [summary])

  // Get active ingredients
  const activeIngredients = useMemo(() => {
    return ingredientsData?.items || []
  }, [ingredientsData])

  // Initialize inventory from summary data
  useEffect(() => {
    if (summary?.usage_items && activeIngredients.length > 0) {
      const initialInventory: Record<number, string> = {}
      summary.usage_items.forEach((item) => {
        initialInventory[item.ingredient_id] = item.opening_quantity.toString()
      })
      setInventory(initialInventory)
      setIsDirty(false)
    }
  }, [summary, activeIngredients])

  // Handle inventory value change
  const handleInventoryChange = useCallback((ingredientId: number, value: string) => {
    setInventory((prev) => ({ ...prev, [ingredientId]: value }))
    setIsDirty(true)
    // Clear error for this field
    if (errors[ingredientId]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[ingredientId]
        return newErrors
      })
    }
  }, [errors])

  // Copy from previous closing
  const handleCopyFromPreviousClosing = useCallback(() => {
    const newInventory: Record<number, string> = {}
    activeIngredients.forEach((ingredient) => {
      const previousItem = previousClosingMap[ingredient.id]
      if (previousItem) {
        newInventory[ingredient.id] = previousItem.quantity.toString()
      }
    })
    setInventory(newInventory)
    setIsDirty(true)
    setErrors({})
    showSuccess(t('openDayModal.copiedValues'))
  }, [activeIngredients, previousClosingMap, showSuccess, t])

  // Validate form
  const validateForm = useCallback((): boolean => {
    const newErrors: Record<number, string> = {}
    let isValid = true

    activeIngredients.forEach((ingredient) => {
      const value = inventory[ingredient.id]
      if (value === undefined || value === '') {
        newErrors[ingredient.id] = t('validation.required')
        isValid = false
      } else {
        const numValue = parseFloat(value)
        if (isNaN(numValue)) {
          newErrors[ingredient.id] = t('openDayModal.invalidValue')
          isValid = false
        } else if (numValue < 0) {
          newErrors[ingredient.id] = t('openDayModal.cannotBeNegative')
          isValid = false
        }
      }
    })

    setErrors(newErrors)
    return isValid
  }, [activeIngredients, inventory, t])

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: () => {
      const inventoryItems = activeIngredients.map((ingredient) => ({
        ingredient_id: ingredient.id,
        quantity: parseFloat(inventory[ingredient.id] || '0'),
      }))
      return updateOpeningInventory(dayId, inventoryItems)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daySummary', dayId] })
      setIsDirty(false)
      showSuccess(t('common.save'))
    },
    onError: (error: Error) => {
      showError(error.message || t('errors.generic'))
    },
  })

  // Handle save
  const handleSave = useCallback(() => {
    if (!validateForm()) {
      return
    }
    saveMutation.mutate()
  }, [validateForm, saveMutation])

  // Get unit label for ingredient
  const getUnitLabel = (ingredient: Ingredient): string => {
    return ingredient.unit_type === 'weight' ? 'kg' : 'szt'
  }

  // Calculate difference between opening and previous closing
  const getDifference = (ingredientId: number): number | null => {
    const openingValue = parseFloat(inventory[ingredientId] || '0')
    const previousValue = previousClosingMap[ingredientId]?.quantity
    if (previousValue === undefined) return null
    return openingValue - previousValue
  }

  const isLoading = summaryLoading || ingredientsLoading

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    )
  }

  if (summaryError) {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
        <p className="text-red-800">{t('errors.generic')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            {t('wizard.openingInventory')}
          </h3>
        </div>

        {isEditable && previousClosing?.date && (
          <button
            type="button"
            onClick={handleCopyFromPreviousClosing}
            className="btn btn-secondary flex items-center gap-2 text-sm"
          >
            <Copy className="w-4 h-4" />
            {t('openDayModal.copyFromLastClose')}
          </button>
        )}
      </div>

      {/* Info message */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          {isEditable
            ? t('wizard.infoOpeningValues')
            : t('wizard.infoOpeningValues')}
        </p>
      </div>

      {/* Ingredients table */}
      {activeIngredients.length === 0 ? (
        <div className="empty-state py-8">
          <p className="empty-state-title">{t('openDayModal.noIngredients')}</p>
          <p className="empty-state-description">
            {t('openDayModal.addIngredientsFirst')}
          </p>
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {t('menu.ingredient')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {t('openDayModal.unit')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {t('wizard.previousClosing')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {t('wizard.openingQty')}
                    {isEditable && ' *'}
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {t('inventory.difference')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {activeIngredients.map((ingredient) => {
                  const previousItem = previousClosingMap[ingredient.id]
                  const openingItem = openingValuesMap[ingredient.id]
                  const hasError = !!errors[ingredient.id]
                  const difference = getDifference(ingredient.id)

                  return (
                    <tr
                      key={ingredient.id}
                      className={hasError ? 'bg-red-50' : undefined}
                    >
                      <td className="px-4 py-3">
                        <span className="font-medium text-gray-900">
                          {ingredient.name}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {getUnitLabel(ingredient)}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-500">
                        {previousItem
                          ? formatQuantity(
                              previousItem.quantity,
                              ingredient.unit_type,
                              previousItem.unit_label
                            )
                          : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col items-end">
                          {isEditable ? (
                            <>
                              <input
                                type="number"
                                min="0"
                                step={ingredient.unit_type === 'weight' ? '0.01' : '1'}
                                value={inventory[ingredient.id] || ''}
                                onChange={(e) =>
                                  handleInventoryChange(ingredient.id, e.target.value)
                                }
                                className={`input w-28 text-right ${
                                  hasError
                                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                                    : ''
                                }`}
                                placeholder="0"
                                aria-invalid={hasError}
                                aria-describedby={
                                  hasError ? `error-${ingredient.id}` : undefined
                                }
                              />
                              {hasError && (
                                <span
                                  id={`error-${ingredient.id}`}
                                  className="text-xs text-red-600 mt-1"
                                  role="alert"
                                >
                                  {errors[ingredient.id]}
                                </span>
                              )}
                            </>
                          ) : (
                            <span className="font-medium text-gray-900">
                              {openingItem
                                ? formatQuantity(
                                    openingItem.opening_quantity,
                                    ingredient.unit_type,
                                    openingItem.unit_label
                                  )
                                : inventory[ingredient.id]
                                ? formatQuantity(
                                    parseFloat(inventory[ingredient.id]),
                                    ingredient.unit_type,
                                    getUnitLabel(ingredient)
                                  )
                                : '-'}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {difference !== null && (
                          <div className="flex items-center justify-center gap-1">
                            <ArrowRight className="w-3 h-3 text-gray-400" />
                            <span
                              className={`text-sm font-medium ${
                                difference > 0
                                  ? 'text-green-600'
                                  : difference < 0
                                  ? 'text-red-600'
                                  : 'text-gray-500'
                              }`}
                            >
                              {difference > 0 ? '+' : ''}
                              {formatQuantity(
                                difference,
                                ingredient.unit_type,
                                getUnitLabel(ingredient)
                              )}
                            </span>
                          </div>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Previous day comparison info */}
      {previousClosing?.date && (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-600">
            {t('wizard.previousDayInfo')}
          </p>
        </div>
      )}

      {/* Save button (only if editable and dirty) */}
      {isEditable && isDirty && (
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="btn btn-primary flex items-center gap-2"
          >
            {saveMutation.isPending ? (
              <>
                <LoadingSpinner size="sm" inline />
                {t('common.saving')}
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                {t('common.save')}
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}
