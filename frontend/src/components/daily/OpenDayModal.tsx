import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Copy, AlertCircle } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import { getIngredients } from '../../api/ingredients'
import { getPreviousClosing, openDay, checkPreviousDayStatus } from '../../api/dailyOperations'
import { getTodayDateString, formatDate, formatQuantity } from '../../utils/formatters'
import type { Ingredient, InventorySnapshotItem, PreviousClosingItem } from '../../types'

interface OpenDayModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function OpenDayModal({ isOpen, onClose, onSuccess }: OpenDayModalProps) {
  const queryClient = useQueryClient()
  const [date, setDate] = useState(getTodayDateString())
  const [inventory, setInventory] = useState<Record<number, string>>({})
  const [errors, setErrors] = useState<Record<number, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Fetch ingredients
  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
    enabled: isOpen,
  })

  // Fetch previous closing values
  const { data: previousClosing, isLoading: previousClosingLoading } = useQuery({
    queryKey: ['previousClosing'],
    queryFn: getPreviousClosing,
    enabled: isOpen,
  })

  // Check if previous day needs closing
  const { data: previousDayStatus } = useQuery({
    queryKey: ['previousDayStatus'],
    queryFn: checkPreviousDayStatus,
    enabled: isOpen,
  })

  // Open day mutation
  const openDayMutation = useMutation({
    mutationFn: openDay,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todayRecord'] })
      queryClient.invalidateQueries({ queryKey: ['recentDays'] })
      onSuccess()
      onClose()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      setGeneralError(error.response?.data?.detail || 'Wystapil blad podczas otwierania dnia')
    },
  })

  // Create a map of previous closing values by ingredient ID
  const previousClosingMap = useMemo(() => {
    const map: Record<number, PreviousClosingItem> = {}
    if (previousClosing?.items) {
      previousClosing.items.forEach((item) => {
        map[item.ingredient_id] = item
      })
    }
    return map
  }, [previousClosing])

  // Get active ingredients
  const activeIngredients = useMemo(() => {
    return ingredientsData?.items || []
  }, [ingredientsData])

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setDate(getTodayDateString())
      setInventory({})
      setErrors({})
      setGeneralError(null)
    }
  }, [isOpen])

  // Copy from last closing
  const handleCopyFromLastClosing = () => {
    const newInventory: Record<number, string> = {}
    activeIngredients.forEach((ingredient) => {
      const previousItem = previousClosingMap[ingredient.id]
      if (previousItem) {
        newInventory[ingredient.id] = previousItem.quantity.toString()
      }
    })
    setInventory(newInventory)
    setErrors({})
  }

  // Update inventory value
  const handleInventoryChange = (ingredientId: number, value: string) => {
    setInventory((prev) => ({ ...prev, [ingredientId]: value }))
    // Clear error for this field
    if (errors[ingredientId]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[ingredientId]
        return newErrors
      })
    }
  }

  // Get unit label for ingredient
  const getUnitLabel = (ingredient: Ingredient): string => {
    return ingredient.unit_type === 'weight' ? 'kg' : 'szt'
  }

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<number, string> = {}
    let isValid = true

    activeIngredients.forEach((ingredient) => {
      const value = inventory[ingredient.id]
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

  // Handle form submission
  const handleSubmit = () => {
    setGeneralError(null)

    if (!validateForm()) {
      setGeneralError('Wszystkie skladniki musza miec uzupelniona ilosc')
      return
    }

    const openingInventory: InventorySnapshotItem[] = activeIngredients.map((ingredient) => ({
      ingredient_id: ingredient.id,
      quantity: parseFloat(inventory[ingredient.id] || '0'),
    }))

    openDayMutation.mutate({
      date,
      opening_inventory: openingInventory,
    })
  }

  const isLoading = ingredientsLoading || previousClosingLoading

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Otworz dzien" size="xl">
      {isLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Previous day warning */}
          {previousDayStatus?.needs_closing && (
            <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-yellow-800">
                  Poprzedni dzien nie zostal zamkniety
                </p>
                <p className="text-sm text-yellow-700 mt-1">
                  Data: {previousDayStatus.previous_date ? formatDate(previousDayStatus.previous_date) : 'Nieznana'}
                </p>
                <p className="text-sm text-yellow-600 mt-1">
                  Zalecamy najpierw zamknac poprzedni dzien.
                </p>
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

          {/* Date picker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Previous closing info */}
          {previousClosing?.date && (
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600">
                Ostatnie zamkniecie: {formatDate(previousClosing.date)}
              </div>
              <button
                type="button"
                onClick={handleCopyFromLastClosing}
                className="btn btn-secondary flex items-center gap-2 text-sm"
              >
                <Copy className="w-4 h-4" />
                Kopiuj z ostatniego zamkniecia
              </button>
            </div>
          )}

          {/* Ingredients table */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Stany poczatkowe skladnikow
            </h3>
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Skladnik
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Jednostka
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      Ostatnie zamkniecie
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      Stan poczatkowy
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {activeIngredients.map((ingredient) => {
                    const previousItem = previousClosingMap[ingredient.id]
                    const hasError = !!errors[ingredient.id]

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
                            ? formatQuantity(previousItem.quantity, ingredient.unit_type)
                            : '-'}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-col items-end">
                            <input
                              type="number"
                              min="0"
                              step={ingredient.unit_type === 'weight' ? '0.01' : '1'}
                              value={inventory[ingredient.id] || ''}
                              onChange={(e) =>
                                handleInventoryChange(ingredient.id, e.target.value)
                              }
                              className={`input w-24 text-right ${
                                hasError ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
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

          {/* Action buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary flex-1"
            >
              Anuluj
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={openDayMutation.isPending}
              className="btn btn-primary flex-1 flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4" />
              {openDayMutation.isPending ? 'Otwieranie...' : 'Otworz dzien'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}
