import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Square, AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react'
import Modal from '../common/Modal'
import ConfirmDialog from '../common/ConfirmDialog'
import LoadingSpinner from '../common/LoadingSpinner'
import { useToast } from '../../context/ToastContext'
import { getIngredients } from '../../api/ingredients'
import { closeDay, getDaySummary } from '../../api/dailyOperations'
import { formatCurrency, formatDate, formatQuantity } from '../../utils/formatters'
import type {
  DailyRecord,
  Ingredient,
  InventorySnapshotItem,
  UsageItem,
  DiscrepancyAlert,
} from '../../types'

interface CloseDayModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  dailyRecord: DailyRecord
}

interface ClosingInventoryState {
  [ingredientId: number]: string
}

export default function CloseDayModal({
  isOpen,
  onClose,
  onSuccess,
  dailyRecord,
}: CloseDayModalProps) {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [closingInventory, setClosingInventory] = useState<ClosingInventoryState>({})
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<Record<number, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [showCalculation, setShowCalculation] = useState(false)
  const [showConfirmClose, setShowConfirmClose] = useState(false)

  // Fetch ingredients
  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
    enabled: isOpen,
  })

  // Fetch day summary (includes opening counts, events, etc.)
  const { data: daySummary, isLoading: summaryLoading } = useQuery({
    queryKey: ['daySummary', dailyRecord.id],
    queryFn: () => getDaySummary(dailyRecord.id),
    enabled: isOpen,
  })

  // Close day mutation
  const closeDayMutation = useMutation({
    mutationFn: ({
      inventory,
      notes,
    }: {
      inventory: InventorySnapshotItem[]
      notes?: string
    }) => closeDay(dailyRecord.id, inventory, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todayRecord'] })
      queryClient.invalidateQueries({ queryKey: ['recentDays'] })
      queryClient.invalidateQueries({ queryKey: ['daySummary'] })
      showSuccess('Dzien zostal zamkniety')
      onSuccess()
      onClose()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || 'Wystapil blad podczas zamykania dnia'
      setGeneralError(message)
      showError(message)
      setShowConfirmClose(false)
    },
  })

  // Create a map of usage items by ingredient ID
  const usageItemsMap = useMemo(() => {
    const map: Record<number, UsageItem> = {}
    if (daySummary?.usage_items) {
      daySummary.usage_items.forEach((item) => {
        map[item.ingredient_id] = item
      })
    }
    return map
  }, [daySummary])

  // Get active ingredients
  const activeIngredients = useMemo(() => {
    return ingredientsData?.items || []
  }, [ingredientsData])

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setClosingInventory({})
      setNotes('')
      setErrors({})
      setGeneralError(null)
      setShowCalculation(false)
      setShowConfirmClose(false)
    }
  }, [isOpen])

  // Update closing inventory value
  const handleInventoryChange = (ingredientId: number, value: string) => {
    setClosingInventory((prev) => ({ ...prev, [ingredientId]: value }))
    // Clear error for this field
    if (errors[ingredientId]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[ingredientId]
        return newErrors
      })
    }
    // Reset calculation display when values change
    setShowCalculation(false)
  }

  // Get unit label for ingredient
  const getUnitLabel = (ingredient: Ingredient): string => {
    return ingredient.unit_type === 'weight' ? 'kg' : 'szt'
  }

  // Calculate expected closing for an ingredient
  const getExpectedClosing = (ingredientId: number): number => {
    const usageItem = usageItemsMap[ingredientId]
    if (!usageItem) return 0
    return usageItem.expected_closing
  }

  // Calculate usage for an ingredient
  const calculateUsage = (ingredientId: number): number | null => {
    const usageItem = usageItemsMap[ingredientId]
    if (!usageItem) return null

    const closingValue = closingInventory[ingredientId]
    if (closingValue === undefined || closingValue === '') return null

    const closing = parseFloat(closingValue)
    if (isNaN(closing)) return null

    const expected = usageItem.expected_closing
    return expected - closing
  }

  // Calculate discrepancy percentage
  const calculateDiscrepancy = (
    ingredientId: number
  ): { percent: number | null; level: 'ok' | 'warning' | 'critical' | null } => {
    const usage = calculateUsage(ingredientId)
    if (usage === null) return { percent: null, level: null }

    const usageItem = usageItemsMap[ingredientId]
    if (!usageItem || !usageItem.expected_usage) return { percent: null, level: null }

    const expectedUsage = usageItem.expected_usage
    if (expectedUsage === 0) return { percent: null, level: null }

    const discrepancy = Math.abs(usage - expectedUsage)
    const percent = (discrepancy / expectedUsage) * 100

    let level: 'ok' | 'warning' | 'critical'
    if (percent < 5) {
      level = 'ok'
    } else if (percent < 10) {
      level = 'warning'
    } else {
      level = 'critical'
    }

    return { percent, level }
  }

  // Get discrepancy icon
  const getDiscrepancyIcon = (level: 'ok' | 'warning' | 'critical' | null) => {
    switch (level) {
      case 'ok':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return null
    }
  }

  // Get discrepancy color class
  const getDiscrepancyColorClass = (level: 'ok' | 'warning' | 'critical' | null) => {
    switch (level) {
      case 'ok':
        return 'text-green-600 bg-green-50'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50'
      case 'critical':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-500'
    }
  }

  // Copy expected values to closing
  const handleCopyExpected = () => {
    const newInventory: ClosingInventoryState = {}
    activeIngredients.forEach((ingredient) => {
      const expected = getExpectedClosing(ingredient.id)
      newInventory[ingredient.id] = expected.toString()
    })
    setClosingInventory(newInventory)
    setShowCalculation(false)
  }

  // Calculate usage button handler
  const handleCalculateUsage = () => {
    // Validate all fields have values
    const newErrors: Record<number, string> = {}
    let isValid = true

    activeIngredients.forEach((ingredient) => {
      const value = closingInventory[ingredient.id]
      if (value === undefined || value === '') {
        newErrors[ingredient.id] = 'Wymagane'
        isValid = false
      } else {
        const numValue = parseFloat(value)
        if (isNaN(numValue)) {
          newErrors[ingredient.id] = 'Nieprawidlowa wartosc'
          isValid = false
        } else if (numValue < 0) {
          newErrors[ingredient.id] = 'Ilosc nie moze byc ujemna'
          isValid = false
        }
      }
    })

    setErrors(newErrors)

    if (isValid) {
      setShowCalculation(true)
    }
  }

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<number, string> = {}
    let isValid = true

    activeIngredients.forEach((ingredient) => {
      const value = closingInventory[ingredient.id]
      if (value === undefined || value === '') {
        newErrors[ingredient.id] = 'Wymagane'
        isValid = false
      } else {
        const numValue = parseFloat(value)
        if (isNaN(numValue)) {
          newErrors[ingredient.id] = 'Nieprawidlowa wartosc'
          isValid = false
        } else if (numValue < 0) {
          newErrors[ingredient.id] = 'Ilosc nie moze byc ujemna'
          isValid = false
        }
      }
    })

    setErrors(newErrors)
    return isValid
  }

  // Handle form submission - show confirmation first
  const handleSubmit = () => {
    setGeneralError(null)

    if (!validateForm()) {
      setGeneralError('Wszystkie skladniki musza miec uzupelniona ilosc')
      return
    }

    // Show confirmation dialog
    setShowConfirmClose(true)
  }

  // Actually close the day after confirmation
  const handleConfirmClose = () => {
    const inventory: InventorySnapshotItem[] = activeIngredients.map((ingredient) => ({
      ingredient_id: ingredient.id,
      quantity: parseFloat(closingInventory[ingredient.id] || '0'),
    }))

    closeDayMutation.mutate({
      inventory,
      notes: notes || undefined,
    })
  }

  // Collect all discrepancy alerts from calculated values
  const calculatedAlerts = useMemo(() => {
    if (!showCalculation) return []

    const alerts: DiscrepancyAlert[] = []
    activeIngredients.forEach((ingredient) => {
      const { percent, level } = calculateDiscrepancy(ingredient.id)
      if (percent !== null && level && level !== 'ok') {
        alerts.push({
          ingredient_id: ingredient.id,
          ingredient_name: ingredient.name,
          discrepancy_percent: percent,
          level,
          message: `${ingredient.name}: ${percent.toFixed(1)}% - ${level === 'warning' ? 'Ostrzezenie' : 'Krytyczne'}`,
        })
      }
    })
    return alerts
  }, [showCalculation, activeIngredients, closingInventory, usageItemsMap])

  const isLoading = ingredientsLoading || summaryLoading

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Zamknij dzien: ${formatDate(dailyRecord.date)}`} size="2xl">
      {isLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Day summary */}
          {daySummary && (
            <div className="p-4 bg-gray-50 rounded-lg space-y-2">
              <h3 className="font-medium text-gray-900">Podsumowanie dnia</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Otwarcie:</span>{' '}
                  <span className="font-medium">
                    {daySummary.opening_time || '-'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Dostawy:</span>{' '}
                  <span className="font-medium">
                    {daySummary.events.deliveries_count} ({formatCurrency(daySummary.events.deliveries_total_pln)})
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Transfery:</span>{' '}
                  <span className="font-medium">
                    {daySummary.events.transfers_count} pozycji
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Straty:</span>{' '}
                  <span className="font-medium">
                    {daySummary.events.spoilage_count} pozycji
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* General error */}
          {generalError && (
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800">{generalError}</p>
            </div>
          )}

          {/* Inventory table */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">
                Stany koncowe skladnikow
              </h3>
              <button
                type="button"
                onClick={handleCopyExpected}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Kopiuj oczekiwane wartosci
              </button>
            </div>
            <div className="border border-gray-200 rounded-lg overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Skladnik
                    </th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      Otwarcie
                    </th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      +Dost.
                    </th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      +Trans.
                    </th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      -Straty
                    </th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      Oczekiw.
                    </th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      Zamkniecie
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {activeIngredients.map((ingredient) => {
                    const usageItem = usageItemsMap[ingredient.id]
                    const hasError = !!errors[ingredient.id]
                    const unitLabel = getUnitLabel(ingredient)

                    return (
                      <tr
                        key={ingredient.id}
                        className={hasError ? 'bg-red-50' : undefined}
                      >
                        <td className="px-3 py-2">
                          <div className="font-medium text-gray-900">
                            {ingredient.name}
                          </div>
                          <div className="text-xs text-gray-500">{unitLabel}</div>
                        </td>
                        <td className="px-3 py-2 text-right text-gray-600">
                          {usageItem
                            ? formatQuantity(usageItem.opening_quantity, ingredient.unit_type)
                            : '-'}
                        </td>
                        <td className="px-3 py-2 text-right text-green-600">
                          {usageItem && usageItem.deliveries_quantity > 0
                            ? `+${formatQuantity(usageItem.deliveries_quantity, ingredient.unit_type)}`
                            : '-'}
                        </td>
                        <td className="px-3 py-2 text-right text-blue-600">
                          {usageItem && usageItem.transfers_quantity > 0
                            ? `+${formatQuantity(usageItem.transfers_quantity, ingredient.unit_type)}`
                            : '-'}
                        </td>
                        <td className="px-3 py-2 text-right text-red-600">
                          {usageItem && usageItem.spoilage_quantity > 0
                            ? `-${formatQuantity(usageItem.spoilage_quantity, ingredient.unit_type)}`
                            : '-'}
                        </td>
                        <td className="px-3 py-2 text-right font-medium text-gray-900">
                          {usageItem
                            ? formatQuantity(usageItem.expected_closing, ingredient.unit_type)
                            : '-'}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-col items-end">
                            <input
                              type="number"
                              min="0"
                              step={ingredient.unit_type === 'weight' ? '0.01' : '1'}
                              value={closingInventory[ingredient.id] || ''}
                              onChange={(e) =>
                                handleInventoryChange(ingredient.id, e.target.value)
                              }
                              className={`input w-20 text-right text-sm ${
                                hasError
                                  ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                                  : ''
                              }`}
                              placeholder="0"
                            />
                            {hasError && (
                              <span className="text-xs text-red-600 mt-1">
                                {errors[ingredient.id]}
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Calculate usage button */}
          <button
            type="button"
            onClick={handleCalculateUsage}
            className="btn btn-secondary w-full"
          >
            Oblicz zuzycie
          </button>

          {/* Calculation results */}
          {showCalculation && (
            <>
              {/* Usage summary */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                  <h4 className="text-sm font-medium text-gray-700">
                    Obliczone zuzycie
                  </h4>
                </div>
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Skladnik
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                        Zuzycie
                      </th>
                      <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {activeIngredients.map((ingredient) => {
                      const usage = calculateUsage(ingredient.id)
                      const { percent, level } = calculateDiscrepancy(ingredient.id)

                      return (
                        <tr key={ingredient.id}>
                          <td className="px-4 py-2 font-medium text-gray-900">
                            {ingredient.name}
                          </td>
                          <td className="px-4 py-2 text-right text-gray-900">
                            {usage !== null
                              ? formatQuantity(usage, ingredient.unit_type)
                              : '-'}
                          </td>
                          <td className="px-4 py-2">
                            {level && (
                              <div
                                className={`flex items-center justify-center gap-1 px-2 py-1 rounded ${getDiscrepancyColorClass(level)}`}
                              >
                                {getDiscrepancyIcon(level)}
                                <span className="text-xs font-medium">
                                  {percent !== null ? `${percent.toFixed(1)}%` : '-'}
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

              {/* Discrepancy alerts */}
              {calculatedAlerts.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700">Alerty</h4>
                  {calculatedAlerts.map((alert) => (
                    <div
                      key={alert.ingredient_id}
                      className={`flex items-center gap-2 p-3 rounded-lg ${getDiscrepancyColorClass(alert.level)}`}
                    >
                      {getDiscrepancyIcon(alert.level)}
                      <span className="text-sm font-medium">{alert.message}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Calculated sales */}
              {daySummary?.calculated_sales && daySummary.calculated_sales.length > 0 && (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700">
                      Obliczona sprzedaz
                    </h4>
                  </div>
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Produkt
                        </th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                          Ilosc
                        </th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                          Cena
                        </th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                          Przychod
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {daySummary.calculated_sales.map((sale, index) => (
                        <tr key={index}>
                          <td className="px-4 py-2 font-medium text-gray-900">
                            {sale.product_name}
                            {sale.variant_name && ` (${sale.variant_name})`}
                          </td>
                          <td className="px-4 py-2 text-right text-gray-900">
                            {sale.quantity_sold}
                          </td>
                          <td className="px-4 py-2 text-right text-gray-600">
                            {formatCurrency(sale.unit_price_pln)}
                          </td>
                          <td className="px-4 py-2 text-right font-medium text-gray-900">
                            {formatCurrency(sale.revenue_pln)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-50">
                      <tr>
                        <td
                          colSpan={3}
                          className="px-4 py-2 text-right font-medium text-gray-900"
                        >
                          RAZEM:
                        </td>
                        <td className="px-4 py-2 text-right font-bold text-primary-600">
                          {formatCurrency(daySummary.total_income_pln)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notatki (opcjonalne)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="input w-full"
              placeholder="Dodaj notatki do tego dnia..."
            />
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 pt-4 sticky bottom-0 bg-white">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary flex-1"
              disabled={closeDayMutation.isPending}
            >
              Anuluj
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={closeDayMutation.isPending}
              className="btn btn-danger flex-1 flex items-center justify-center gap-2"
            >
              {closeDayMutation.isPending ? (
                <>
                  <LoadingSpinner size="sm" />
                  Zamykanie...
                </>
              ) : (
                <>
                  <Square className="w-4 h-4" />
                  Zamknij dzien
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Close day confirmation dialog */}
      <ConfirmDialog
        isOpen={showConfirmClose}
        onClose={() => setShowConfirmClose(false)}
        onConfirm={handleConfirmClose}
        title="Potwierdz zamkniecie dnia"
        message={`Czy na pewno chcesz zamknac dzien ${formatDate(dailyRecord.date)}? Po zamknieciu nie bedziesz mogl dodawac nowych dostaw, transferow ani strat do tego dnia.`}
        confirmText="Zamknij dzien"
        cancelText="Anuluj"
        variant="danger"
        isLoading={closeDayMutation.isPending}
      />
    </Modal>
  )
}
