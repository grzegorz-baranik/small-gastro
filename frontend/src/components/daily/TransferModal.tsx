import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Package, AlertCircle } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import { getIngredients } from '../../api/ingredients'
import { createTransfer } from '../../api/midDayOperations'
import type { Ingredient } from '../../types'

interface TransferModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  dailyRecordId: number
}

export default function TransferModal({
  isOpen,
  onClose,
  onSuccess,
  dailyRecordId,
}: TransferModalProps) {
  const queryClient = useQueryClient()
  const [ingredientId, setIngredientId] = useState<number | ''>('')
  const [quantity, setQuantity] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Fetch ingredients
  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
    enabled: isOpen,
  })

  // Create transfer mutation
  const createTransferMutation = useMutation({
    mutationFn: createTransfer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfers', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
      onSuccess()
      onClose()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      setGeneralError(error.response?.data?.detail || 'Wystapil blad podczas zapisywania transferu')
    },
  })

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setIngredientId('')
      setQuantity('')
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

    setErrors(newErrors)
    return isValid
  }

  // Handle form submission
  const handleSubmit = () => {
    setGeneralError(null)

    if (!validateForm()) {
      return
    }

    createTransferMutation.mutate({
      daily_record_id: dailyRecordId,
      ingredient_id: ingredientId as number,
      quantity: parseFloat(quantity),
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Transfer z magazynu" size="md">
      {ingredientsLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Info box */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              Transfer z magazynu oznacza przeniesienie skladnika z magazynu glownego do kuchni/punktu sprzedazy.
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
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
              disabled={createTransferMutation.isPending}
              className="btn btn-primary flex-1 flex items-center justify-center gap-2"
            >
              <Package className="w-4 h-4" />
              {createTransferMutation.isPending ? 'Zapisywanie...' : 'Zapisz transfer'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}
