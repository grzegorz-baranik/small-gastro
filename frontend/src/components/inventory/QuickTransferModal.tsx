import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, Store, Warehouse } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'

interface QuickTransferModalProps {
  isOpen: boolean
  onClose: () => void
  ingredientId: number | null
  ingredientName: string
  warehouseQuantity: number
  unitLabel: string
  onSubmit: (quantity: number) => Promise<void>
}

export default function QuickTransferModal({
  isOpen,
  onClose,
  ingredientId,
  ingredientName,
  warehouseQuantity,
  unitLabel,
  onSubmit,
}: QuickTransferModalProps) {
  const { t } = useTranslation()
  const [quantity, setQuantity] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuantity('')
      setError(null)
      setGeneralError(null)
      setIsSubmitting(false)
    }
  }, [isOpen])

  // Validate form
  const validateForm = (): boolean => {
    if (!quantity || quantity === '') {
      setError(t('validation.required'))
      return false
    }

    const numQuantity = parseFloat(quantity)
    if (isNaN(numQuantity)) {
      setError(t('validation.invalidValue'))
      return false
    }

    if (numQuantity <= 0) {
      setError(t('validation.mustBePositive'))
      return false
    }

    if (numQuantity > warehouseQuantity) {
      setError(t('transferModal.quantityMustBePositive'))
      return false
    }

    setError(null)
    return true
  }

  // Handle form submission
  const handleSubmit = async () => {
    setGeneralError(null)

    if (!validateForm() || !ingredientId) {
      return
    }

    setIsSubmitting(true)

    try {
      await onSubmit(parseFloat(quantity))
      onClose()
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      const message = error.response?.data?.detail || t('inventory.transfer.error')
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

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${t('inventory.transfer.title')} - ${ingredientName}`}
      size="sm"
    >
      <div className="space-y-4">
        {/* General error */}
        {generalError && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{generalError}</p>
          </div>
        )}

        {/* Available quantity display */}
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center gap-2 text-amber-800 mb-1">
            <Warehouse className="w-4 h-4" />
            <span className="text-sm font-medium">{t('inventory.transfer.available')}</span>
          </div>
          <p className="text-lg font-semibold text-amber-900">
            {formatQty(warehouseQuantity)}
          </p>
        </div>

        {/* Quantity Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
            {t('inventory.transfer.quantity')} ({unitLabel})
          </label>
          <input
            type="number"
            min="0"
            max={warehouseQuantity}
            step={unitLabel === 'kg' || unitLabel === 'g' ? '0.01' : '1'}
            value={quantity}
            onChange={(e) => {
              setQuantity(e.target.value)
              if (error) {
                setError(null)
              }
            }}
            className={`input w-full ${error ? 'border-red-500' : ''}`}
            placeholder="0"
          />
          {error && (
            <p className="text-xs text-red-600 mt-1">{error}</p>
          )}
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
            disabled={isSubmitting || warehouseQuantity <= 0}
            className="btn btn-primary flex-1 flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" inline />
                {t('common.saving')}
              </>
            ) : (
              <>
                <Store className="w-4 h-4" />
                {t('inventory.transfer.toShop')}
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  )
}
