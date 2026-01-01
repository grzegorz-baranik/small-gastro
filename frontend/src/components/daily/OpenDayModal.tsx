import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Copy, AlertCircle, AlertTriangle } from 'lucide-react'
import Modal from '../common/Modal'
import ConfirmDialog from '../common/ConfirmDialog'
import LoadingSpinner from '../common/LoadingSpinner'
import { useToast } from '../../context/ToastContext'
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
  const { showSuccess, showError } = useToast()
  const [date, setDate] = useState(getTodayDateString())
  const [inventory, setInventory] = useState<Record<number, string>>({})
  const [errors, setErrors] = useState<Record<number, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [showPreviousDayWarning, setShowPreviousDayWarning] = useState(false)

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
      showSuccess('Dzien zostal otwarty')
      onSuccess()
      onClose()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || 'Wystapil blad podczas otwierania dnia'
      setGeneralError(message)
      showError(message)
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
      setShowPreviousDayWarning(false)
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
    showSuccess('Skopiowano wartosci z ostatniego zamkniecia')
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

    // Check if previous day warning should be shown
    if (previousDayStatus?.needs_closing && !showPreviousDayWarning) {
      setShowPreviousDayWarning(true)
      return
    }

    submitForm()
  }

  const submitForm = () => {
    const openingInventory: InventorySnapshotItem[] = activeIngredients.map((ingredient) => ({
      ingredient_id: ingredient.id,
      quantity: parseFloat(inventory[ingredient.id] || '0'),
    }))

    openDayMutation.mutate({
      date,
      opening_inventory: openingInventory,
    })
  }

  const handleConfirmOpenDespiteWarning = () => {
    setShowPreviousDayWarning(false)
    submitForm()
  }

  const isLoading = ingredientsLoading || previousClosingLoading

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="Otworz dzien"
        size="xl"
        preventClose={openDayMutation.isPending}
      >
        {isLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSubmit()
            }}
            className="space-y-4"
          >
            {/* Previous day warning - inline version */}
            {previousDayStatus?.needs_closing && !showPreviousDayWarning && (
              <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
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
              <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
                Data
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="input w-full"
                required
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
              <h3 className="text-sm font-medium text-gray-700 mb-2 label-required">
                Stany poczatkowe skladnikow
              </h3>
              {activeIngredients.length === 0 ? (
                <div className="empty-state py-8">
                  <p className="empty-state-title">Brak skladnikow</p>
                  <p className="empty-state-description">
                    Dodaj skladniki w menu, aby moc otworzyc dzien.
                  </p>
                </div>
              ) : (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
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
                            Stan poczatkowy *
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
                                    required
                                    aria-invalid={hasError}
                                    aria-describedby={hasError ? `error-${ingredient.id}` : undefined}
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
                                </div>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary flex-1"
                disabled={openDayMutation.isPending}
              >
                Anuluj
              </button>
              <button
                type="submit"
                disabled={openDayMutation.isPending || activeIngredients.length === 0}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {openDayMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Otwieranie...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Otworz dzien
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </Modal>

      {/* Previous day warning confirmation dialog */}
      <ConfirmDialog
        isOpen={showPreviousDayWarning}
        onClose={() => setShowPreviousDayWarning(false)}
        onConfirm={handleConfirmOpenDespiteWarning}
        title="Poprzedni dzien nie jest zamkniety"
        message={`Poprzedni dzien (${previousDayStatus?.previous_date ? formatDate(previousDayStatus.previous_date) : 'nieznany'}) nie zostal zamkniety. Czy na pewno chcesz kontynuowac i otworzyc nowy dzien? Zalecamy najpierw zamknac poprzedni dzien dla zachowania spojnosci danych.`}
        confirmText="Kontynuuj mimo to"
        cancelText="Zamknij poprzedni dzien"
        variant="warning"
        isLoading={openDayMutation.isPending}
      />
    </>
  )
}
