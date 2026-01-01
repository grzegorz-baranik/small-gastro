import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, AlertCircle } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import { useToast } from '../../context/ToastContext'
import { getIngredients } from '../../api/ingredients'
import { createSpoilage } from '../../api/midDayOperations'
import type { Ingredient, SpoilageReason } from '../../types'

interface SpoilageModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  dailyRecordId: number
}

// Spoilage reason labels in Polish
const SPOILAGE_REASON_LABELS: Record<SpoilageReason, string> = {
  expired: 'Przeterminowane',
  damaged: 'Uszkodzone',
  quality: 'Jakosc',
  other: 'Inne',
}

export default function SpoilageModal({
  isOpen,
  onClose,
  onSuccess,
  dailyRecordId,
}: SpoilageModalProps) {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [ingredientId, setIngredientId] = useState<number | ''>('')
  const [quantity, setQuantity] = useState('')
  const [reason, setReason] = useState<SpoilageReason | ''>('')
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Fetch ingredients
  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
    enabled: isOpen,
  })

  // Create spoilage mutation
  const createSpoilageMutation = useMutation({
    mutationFn: createSpoilage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['spoilage', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
      showSuccess('Strata zostala zapisana')
      onSuccess()
      onClose()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || 'Wystapil blad podczas zapisywania straty'
      setGeneralError(message)
      showError(message)
    },
  })

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setIngredientId('')
      setQuantity('')
      setReason('')
      setNotes('')
      setErrors({})
      setGeneralError(null)
    }
  }, [isOpen])

  // Get selected ingredient details
  const selectedIngredient = ingredientsData?.items.find(
    (ing: Ingredient) => ing.id === ingredientId
  )

  // Get unit label for ingredient
  const getUnitLabel = (ingredient: Ingredient): string => {
    return ingredient.unit_type === 'weight' ? 'kg' : 'szt'
  }

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}
    let isValid = true

    if (!ingredientId) {
      newErrors.ingredientId = 'Wybierz skladnik'
      isValid = false
    }

    if (!quantity || quantity === '') {
      newErrors.quantity = 'Podaj ilosc'
      isValid = false
    } else {
      const numQuantity = parseFloat(quantity)
      if (isNaN(numQuantity) || numQuantity <= 0) {
        newErrors.quantity = 'Ilosc musi byc wieksza od 0'
        isValid = false
      }
    }

    if (!reason) {
      newErrors.reason = 'Wybierz powod'
      isValid = false
    }

    setErrors(newErrors)
    return isValid
  }

  // Handle form submission
  const handleSubmit = () => {
    setGeneralError(null)

    if (!validateForm()) {
      return
    }

    createSpoilageMutation.mutate({
      daily_record_id: dailyRecordId,
      ingredient_id: ingredientId as number,
      quantity: parseFloat(quantity),
      reason: reason as SpoilageReason,
      notes: notes.trim() || undefined,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Zapisz straty" size="md">
      {ingredientsLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Warning box */}
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">
              Straty to skladniki, ktore nie moga byc wykorzystane z powodu uszkodzenia, przeterminowania lub innych przyczyn.
            </p>
          </div>

          {/* General error */}
          {generalError && (
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800">{generalError}</p>
            </div>
          )}

          {/* Ingredient select */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
              Skladnik
            </label>
            <select
              value={ingredientId}
              onChange={(e) => {
                setIngredientId(e.target.value ? parseInt(e.target.value) : '')
                if (errors.ingredientId) {
                  setErrors((prev) => {
                    const newErrors = { ...prev }
                    delete newErrors.ingredientId
                    return newErrors
                  })
                }
              }}
              className={`input w-full ${errors.ingredientId ? 'border-red-500' : ''}`}
            >
              <option value="">Wybierz skladnik...</option>
              {ingredientsData?.items.map((ingredient: Ingredient) => (
                <option key={ingredient.id} value={ingredient.id}>
                  {ingredient.name} ({getUnitLabel(ingredient)})
                </option>
              ))}
            </select>
            {errors.ingredientId && (
              <p className="text-xs text-red-600 mt-1">{errors.ingredientId}</p>
            )}
          </div>

          {/* Quantity input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
              Ilosc {selectedIngredient && `(${getUnitLabel(selectedIngredient)})`}
            </label>
            <input
              type="number"
              min="0"
              step={selectedIngredient?.unit_type === 'weight' ? '0.01' : '1'}
              value={quantity}
              onChange={(e) => {
                setQuantity(e.target.value)
                if (errors.quantity) {
                  setErrors((prev) => {
                    const newErrors = { ...prev }
                    delete newErrors.quantity
                    return newErrors
                  })
                }
              }}
              className={`input w-full ${errors.quantity ? 'border-red-500' : ''}`}
              placeholder="0"
            />
            {errors.quantity && (
              <p className="text-xs text-red-600 mt-1">{errors.quantity}</p>
            )}
          </div>

          {/* Reason select */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
              Powod straty
            </label>
            <select
              value={reason}
              onChange={(e) => {
                setReason(e.target.value as SpoilageReason | '')
                if (errors.reason) {
                  setErrors((prev) => {
                    const newErrors = { ...prev }
                    delete newErrors.reason
                    return newErrors
                  })
                }
              }}
              className={`input w-full ${errors.reason ? 'border-red-500' : ''}`}
            >
              <option value="">Wybierz powod...</option>
              {(Object.keys(SPOILAGE_REASON_LABELS) as SpoilageReason[]).map((key) => (
                <option key={key} value={key}>
                  {SPOILAGE_REASON_LABELS[key]}
                </option>
              ))}
            </select>
            {errors.reason && (
              <p className="text-xs text-red-600 mt-1">{errors.reason}</p>
            )}
          </div>

          {/* Notes input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notatki (opcjonalne)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="input w-full"
              rows={3}
              placeholder="Dodatkowe informacje o stracie..."
            />
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary flex-1"
              disabled={createSpoilageMutation.isPending}
            >
              Anuluj
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={createSpoilageMutation.isPending}
              className="btn btn-danger flex-1 flex items-center justify-center gap-2"
            >
              {createSpoilageMutation.isPending ? (
                <>
                  <LoadingSpinner size="sm" />
                  Zapisywanie...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4" />
                  Zapisz strate
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}
