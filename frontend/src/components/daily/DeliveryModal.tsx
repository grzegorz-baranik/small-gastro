import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Truck, AlertCircle, Plus, Trash2, ArrowLeft, ArrowRight, Warehouse, Store } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import { useToast } from '../../context/ToastContext'
import { getIngredients } from '../../api/ingredients'
import { createDelivery } from '../../api/midDayOperations'
import type { Ingredient, DeliveryItemCreate, DeliveryDestination } from '../../types'

interface DeliveryModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  dailyRecordId: number
}

interface DeliveryItemFormData {
  id: number // temporary ID for React key
  ingredient_id: number | ''
  quantity: string
  cost_pln: string
  expiry_date: string
}

type Step = 'items' | 'details'

export default function DeliveryModal({
  isOpen,
  onClose,
  onSuccess,
  dailyRecordId,
}: DeliveryModalProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  // Multi-step state
  const [step, setStep] = useState<Step>('items')

  // Items step
  const [items, setItems] = useState<DeliveryItemFormData[]>([])
  const [nextItemId, setNextItemId] = useState(1)

  // Details step
  const [destination, setDestination] = useState<DeliveryDestination>('storage')
  const [supplierName, setSupplierName] = useState('')
  const [invoiceNumber, setInvoiceNumber] = useState('')
  const [totalCostPln, setTotalCostPln] = useState('')
  const [notes, setNotes] = useState('')

  // Errors
  const [itemErrors, setItemErrors] = useState<Record<number, Record<string, string>>>({})
  const [detailsErrors, setDetailsErrors] = useState<Record<string, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Fetch ingredients
  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
    enabled: isOpen,
  })

  // Create delivery mutation
  const createDeliveryMutation = useMutation({
    mutationFn: createDelivery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      showSuccess(t('deliveryModal.deliveryAdded'))
      onSuccess()
      onClose()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('deliveryModal.errorSaving')
      setGeneralError(message)
      showError(message)
    },
  })

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep('items')
      setItems([{ id: 1, ingredient_id: '', quantity: '', cost_pln: '', expiry_date: '' }])
      setNextItemId(2)
      setDestination('storage')
      setSupplierName('')
      setInvoiceNumber('')
      setTotalCostPln('')
      setNotes('')
      setItemErrors({})
      setDetailsErrors({})
      setGeneralError(null)
    }
  }, [isOpen])

  // Get ingredient by ID
  const getIngredient = (id: number): Ingredient | undefined => {
    return ingredientsData?.items.find((ing: Ingredient) => ing.id === id)
  }

  // Get unit label for ingredient
  const getUnitLabel = (ingredient: Ingredient): string => {
    return ingredient.unit_type === 'weight' ? 'kg' : 'szt'
  }

  // Add new item row
  const addItem = () => {
    setItems([...items, { id: nextItemId, ingredient_id: '', quantity: '', cost_pln: '', expiry_date: '' }])
    setNextItemId(nextItemId + 1)
  }

  // Remove item row
  const removeItem = (itemId: number) => {
    if (items.length > 1) {
      setItems(items.filter(item => item.id !== itemId))
      // Clear errors for removed item
      const newItemErrors = { ...itemErrors }
      delete newItemErrors[itemId]
      setItemErrors(newItemErrors)
    }
  }

  // Update item field
  const updateItem = (itemId: number, field: keyof DeliveryItemFormData, value: string | number) => {
    setItems(items.map(item =>
      item.id === itemId ? { ...item, [field]: value } : item
    ))
    // Clear field error
    if (itemErrors[itemId]?.[field]) {
      const newItemErrors = { ...itemErrors }
      delete newItemErrors[itemId][field]
      setItemErrors(newItemErrors)
    }
  }

  // Validate items step
  const validateItemsStep = (): boolean => {
    const newErrors: Record<number, Record<string, string>> = {}
    let isValid = true

    items.forEach(item => {
      const errors: Record<string, string> = {}

      if (!item.ingredient_id) {
        errors.ingredient_id = t('deliveryModal.selectIngredientError')
        isValid = false
      }

      if (!item.quantity || item.quantity === '') {
        errors.quantity = t('deliveryModal.enterQuantity')
        isValid = false
      } else {
        const numQuantity = parseFloat(item.quantity)
        if (isNaN(numQuantity) || numQuantity <= 0) {
          errors.quantity = t('deliveryModal.quantityMustBePositive')
          isValid = false
        }
      }

      if (Object.keys(errors).length > 0) {
        newErrors[item.id] = errors
      }
    })

    setItemErrors(newErrors)
    return isValid
  }

  // Validate details step
  const validateDetailsStep = (): boolean => {
    const errors: Record<string, string> = {}
    let isValid = true

    if (!totalCostPln || totalCostPln === '') {
      errors.totalCostPln = t('deliveryModal.enterPrice')
      isValid = false
    } else {
      const numCost = parseFloat(totalCostPln)
      if (isNaN(numCost) || numCost < 0) {
        errors.totalCostPln = t('deliveryModal.priceCannotBeNegative')
        isValid = false
      }
    }

    setDetailsErrors(errors)
    return isValid
  }

  // Handle next step
  const handleNextStep = () => {
    if (validateItemsStep()) {
      setStep('details')
    }
  }

  // Handle back step
  const handleBackStep = () => {
    setStep('items')
  }

  // Handle form submission
  const handleSubmit = () => {
    setGeneralError(null)

    if (!validateDetailsStep()) {
      return
    }

    // Build delivery items
    const deliveryItems: DeliveryItemCreate[] = items.map(item => ({
      ingredient_id: item.ingredient_id as number,
      quantity: parseFloat(item.quantity),
      cost_pln: item.cost_pln ? parseFloat(item.cost_pln) : undefined,
      expiry_date: item.expiry_date || undefined,
    }))

    createDeliveryMutation.mutate({
      daily_record_id: dailyRecordId,
      items: deliveryItems,
      total_cost_pln: parseFloat(totalCostPln),
      destination,
      supplier_name: supplierName || undefined,
      invoice_number: invoiceNumber || undefined,
      notes: notes || undefined,
    })
  }

  // Get modal title based on step
  const getModalTitle = () => {
    if (step === 'items') {
      return `${t('deliveryModal.title')} - ${t('deliveryModal.step1')}`
    }
    return `${t('deliveryModal.title')} - ${t('deliveryModal.step2')}`
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={getModalTitle()} size="lg">
      {ingredientsLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-4">
          {/* General error */}
          {generalError && (
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800">{generalError}</p>
            </div>
          )}

          {step === 'items' && (
            <>
              {/* Items table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-700">
                    {t('deliveryModal.ingredientsList')} ({items.length})
                  </h3>
                  <button
                    type="button"
                    onClick={addItem}
                    className="btn btn-secondary btn-sm flex items-center gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    {t('deliveryModal.addIngredient')}
                  </button>
                </div>

                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {items.map((item, index) => {
                    const selectedIngredient = item.ingredient_id ? getIngredient(item.ingredient_id as number) : undefined
                    const errors = itemErrors[item.id] || {}

                    return (
                      <div key={item.id} className="flex gap-3 items-start p-3 bg-gray-50 rounded-lg">
                        <span className="text-sm text-gray-500 pt-2">{index + 1}.</span>

                        {/* Ingredient select */}
                        <div className="flex-1">
                          <select
                            value={item.ingredient_id}
                            onChange={(e) => updateItem(item.id, 'ingredient_id', e.target.value ? parseInt(e.target.value) : '')}
                            className={`input w-full ${errors.ingredient_id ? 'border-red-500' : ''}`}
                          >
                            <option value="">{t('deliveryModal.selectIngredient')}</option>
                            {ingredientsData?.items.map((ingredient: Ingredient) => (
                              <option key={ingredient.id} value={ingredient.id}>
                                {ingredient.name} ({getUnitLabel(ingredient)})
                              </option>
                            ))}
                          </select>
                          {errors.ingredient_id && (
                            <p className="text-xs text-red-600 mt-1">{errors.ingredient_id}</p>
                          )}
                        </div>

                        {/* Quantity input */}
                        <div className="w-28">
                          <input
                            type="number"
                            min="0"
                            step={selectedIngredient?.unit_type === 'weight' ? '0.01' : '1'}
                            value={item.quantity}
                            onChange={(e) => updateItem(item.id, 'quantity', e.target.value)}
                            placeholder={selectedIngredient ? getUnitLabel(selectedIngredient) : t('deliveryModal.quantity')}
                            className={`input w-full ${errors.quantity ? 'border-red-500' : ''}`}
                          />
                          {errors.quantity && (
                            <p className="text-xs text-red-600 mt-1">{errors.quantity}</p>
                          )}
                        </div>

                        {/* Per-item cost (optional) */}
                        <div className="w-28">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={item.cost_pln}
                            onChange={(e) => updateItem(item.id, 'cost_pln', e.target.value)}
                            placeholder={t('deliveryModal.costOptional')}
                            className="input w-full"
                          />
                        </div>

                        {/* Expiry date (optional) */}
                        <div className="w-36">
                          <input
                            type="date"
                            value={item.expiry_date}
                            onChange={(e) => updateItem(item.id, 'expiry_date', e.target.value)}
                            className="input w-full text-sm"
                            title={t('batch.expiryDateOptional')}
                          />
                        </div>

                        {/* Remove button */}
                        <button
                          type="button"
                          onClick={() => removeItem(item.id)}
                          disabled={items.length === 1}
                          className="p-2 text-gray-400 hover:text-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Step 1 Actions */}
              <div className="flex gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={onClose}
                  className="btn btn-secondary flex-1"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="button"
                  onClick={handleNextStep}
                  className="btn btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  {t('deliveryModal.next')}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </>
          )}

          {step === 'details' && (
            <>
              {/* Items summary */}
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  {t('deliveryModal.itemsCount', { count: items.length })}
                </p>
              </div>

              {/* Destination picker */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('deliveryModal.destination')}
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setDestination('storage')}
                    className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition-colors ${
                      destination === 'storage'
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300 text-gray-600'
                    }`}
                  >
                    <Warehouse className="w-5 h-5" />
                    <span className="font-medium">{t('deliveryModal.toWarehouse')}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDestination('shop')}
                    className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition-colors ${
                      destination === 'shop'
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300 text-gray-600'
                    }`}
                  >
                    <Store className="w-5 h-5" />
                    <span className="font-medium">{t('deliveryModal.toShop')}</span>
                  </button>
                </div>
              </div>

              {/* Supplier name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('deliveryModal.supplierName')} ({t('common.optional')})
                </label>
                <input
                  type="text"
                  value={supplierName}
                  onChange={(e) => setSupplierName(e.target.value)}
                  className="input w-full"
                  placeholder={t('deliveryModal.supplierPlaceholder')}
                />
              </div>

              {/* Invoice number */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('deliveryModal.invoiceNumber')} ({t('common.optional')})
                </label>
                <input
                  type="text"
                  value={invoiceNumber}
                  onChange={(e) => setInvoiceNumber(e.target.value)}
                  className="input w-full"
                  placeholder={t('deliveryModal.invoicePlaceholder')}
                />
              </div>

              {/* Total cost */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 label-required">
                  {t('deliveryModal.totalCost')}
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={totalCostPln}
                  onChange={(e) => {
                    setTotalCostPln(e.target.value)
                    if (detailsErrors.totalCostPln) {
                      setDetailsErrors(prev => {
                        const newErrors = { ...prev }
                        delete newErrors.totalCostPln
                        return newErrors
                      })
                    }
                  }}
                  className={`input w-full ${detailsErrors.totalCostPln ? 'border-red-500' : ''}`}
                  placeholder="0.00"
                />
                {detailsErrors.totalCostPln && (
                  <p className="text-xs text-red-600 mt-1">{detailsErrors.totalCostPln}</p>
                )}
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('deliveryModal.notes')} ({t('common.optional')})
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="input w-full"
                  rows={2}
                  placeholder={t('deliveryModal.notesPlaceholder')}
                />
              </div>

              {/* Step 2 Actions */}
              <div className="flex gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={handleBackStep}
                  className="btn btn-secondary flex items-center gap-2"
                  disabled={createDeliveryMutation.isPending}
                >
                  <ArrowLeft className="w-4 h-4" />
                  {t('deliveryModal.back')}
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={createDeliveryMutation.isPending}
                  className="btn btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  {createDeliveryMutation.isPending ? (
                    <>
                      <LoadingSpinner size="sm" />
                      {t('common.saving')}
                    </>
                  ) : (
                    <>
                      <Truck className="w-4 h-4" />
                      {t('deliveryModal.saveDelivery')}
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </Modal>
  )
}
