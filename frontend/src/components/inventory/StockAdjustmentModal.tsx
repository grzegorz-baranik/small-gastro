import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, Check, ArrowRight } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import type { StockAdjustmentCreate, AdjustmentType } from '../../types'

interface StockAdjustmentModalProps {
  isOpen: boolean
  onClose: () => void
  ingredientId: number | null
  ingredientName: string
  location: 'storage' | 'shop'
  currentQuantity: number
  unitLabel: string
  onSubmit: (data: StockAdjustmentCreate) => Promise<void>
}

// Adjustment reasons matching backend expectations
const ADJUSTMENT_REASONS = [
  { value: 'inventory_count', key: 'inventoryCount' },
  { value: 'damage', key: 'damage' },
  { value: 'loss', key: 'loss' },
  { value: 'other', key: 'other' },
] as const

export default function StockAdjustmentModal({
  isOpen,
  onClose,
  ingredientId,
  ingredientName,
  location,
  currentQuantity,
  unitLabel,
  onSubmit,
}: StockAdjustmentModalProps) {
  const { t } = useTranslation()
  const [adjustmentType, setAdjustmentType] = useState<AdjustmentType>('set')
  const [quantity, setQuantity] = useState('')
  const [reason, setReason] = useState('')
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setAdjustmentType('set')
      setQuantity('')
      setReason('')
      setNotes('')
      setErrors({})
      setGeneralError(null)
      setIsSubmitting(false)
    }
  }, [isOpen])

  // Calculate the new quantity based on adjustment type
  const newQuantity = useMemo(() => {
    const numQuantity = parseFloat(quantity)
    if (isNaN(numQuantity)) return currentQuantity

    switch (adjustmentType) {
      case 'set':
        return numQuantity
      case 'add':
        return currentQuantity + numQuantity
      case 'subtract':
        return currentQuantity - numQuantity
      default:
        return currentQuantity
    }
  }, [adjustmentType, quantity, currentQuantity])

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}
    let isValid = true

    if (!quantity || quantity === '') {
      newErrors.quantity = t('validation.required')
      isValid = false
    } else {
      const numQuantity = parseFloat(quantity)
      if (isNaN(numQuantity)) {
        newErrors.quantity = t('validation.invalidValue')
        isValid = false
      } else if (numQuantity < 0) {
        newErrors.quantity = t('validation.cannotBeNegative')
        isValid = false
      } else if (adjustmentType === 'set' || adjustmentType === 'add') {
        // No additional validation for set/add
      } else if (adjustmentType === 'subtract' && numQuantity > currentQuantity) {
        newErrors.quantity = t('validation.cannotBeNegative')
        isValid = false
      }
    }

    // Check if new quantity would be negative
    if (newQuantity < 0) {
      newErrors.quantity = t('validation.cannotBeNegative')
      isValid = false
    }

    if (!reason) {
      newErrors.reason = t('validation.required')
      isValid = false
    }

    setErrors(newErrors)
    return isValid
  }

  // Handle form submission
  const handleSubmit = async () => {
    setGeneralError(null)

    if (!validateForm() || !ingredientId) {
      return
    }

    setIsSubmitting(true)

    try {
      await onSubmit({
        ingredient_id: ingredientId,
        location,
        adjustment_type: adjustmentType,
        quantity: parseFloat(quantity),
        reason,
        notes: notes.trim() || undefined,
      })
      onClose()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      const message = err.response?.data?.detail || t('inventory.adjustment.error')
      setGeneralError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Format quantity for display
  const formatQty = (value: number): string => {
    if (unitLabel === 'kg' || unitLabel === 'g') {
      return `${value.toFixed(2)} ${unitLabel}`
    }
    return `${Math.round(value)} ${unitLabel}`
  }

  const locationLabel = location === 'storage' ? t('common.storage') : t('common.shop')

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${t('inventory.adjustment.title')} - ${ingredientName} (${locationLabel})`}
      size="md"
    >
      <div className="space-y-4">
        {/* General error */}
        {generalError && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{generalError}</p>
          </div>
        )}

        {/* Adjustment Type Radio Buttons */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {t('inventory.adjustment.type')}
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="adjustmentType"
                value="set"
                checked={adjustmentType === 'set'}
                onChange={() => setAdjustmentType('set')}
                className="w-4 h-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">
                {t('inventory.adjustment.set')}
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="adjustmentType"
                value="add"
                checked={adjustmentType === 'add'}
                onChange={() => setAdjustmentType('add')}
                className="w-4 h-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">
                {t('inventory.adjustment.add')}
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="adjustmentType"
                value="subtract"
                checked={adjustmentType === 'subtract'}
                onChange={() => setAdjustmentType('subtract')}
                className="w-4 h-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">
                {t('inventory.adjustment.subtract')}
              </span>
            </label>
          </div>
        </div>

        {/* Quantity Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
            {t('inventory.adjustment.quantity')} ({unitLabel})
          </label>
          <input
            type="number"
            min="0"
            step={unitLabel === 'kg' || unitLabel === 'g' ? '0.01' : '1'}
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

        {/* Reason Dropdown */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
            {t('inventory.adjustment.reason')}
          </label>
          <select
            value={reason}
            onChange={(e) => {
              setReason(e.target.value)
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
            <option value="">{t('spoilageModal.selectReason')}</option>
            {ADJUSTMENT_REASONS.map((r) => (
              <option key={r.value} value={r.value}>
                {t(`inventory.adjustment.reasons.${r.key}`)}
              </option>
            ))}
          </select>
          {errors.reason && (
            <p className="text-xs text-red-600 mt-1">{errors.reason}</p>
          )}
        </div>

        {/* Notes Textarea */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('inventory.adjustment.notes')}
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="input w-full"
            rows={2}
            placeholder={t('spoilageModal.notesPlaceholder')}
          />
        </div>

        {/* Preview */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm font-medium text-gray-700 mb-2">
            {t('inventory.adjustment.preview')}
          </p>
          <div className="flex items-center justify-center gap-4">
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-1">{t('inventory.adjustment.current')}</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatQty(currentQuantity)}
              </p>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400" />
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-1">{t('inventory.adjustment.new')}</p>
              <p
                className={`text-lg font-semibold ${
                  newQuantity < 0 ? 'text-red-600' : 'text-green-600'
                }`}
              >
                {formatQty(newQuantity)}
              </p>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary flex-1"
            disabled={isSubmitting}
          >
            {t('common.cancel')}
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="btn btn-primary flex-1 flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" inline />
                {t('common.saving')}
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                {t('inventory.adjustment.submit')}
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  )
}
