import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ShoppingCart,
  AlertCircle,
  Clock,
  X,
  Plus,
  Minus,
} from 'lucide-react'
import { useDailyRecord } from '../context/DailyRecordContext'
import {
  getCategories,
  getProductsForSale,
  recordSale,
  getRecentSales,
  getDayTotal,
  voidSale,
} from '../api/recordedSales'
import { formatCurrency } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import type {
  ProductCategory,
  ProductForSale,
  ProductVariantForSale,
  RecordedSale,
  VoidReason,
} from '../types'

// Minimum touch target size for accessibility (48px)
const TOUCH_TARGET_MIN = 'min-h-[48px]'

/**
 * Touch-optimized POS interface for recording sales
 */
export default function SalesEntryPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { openRecord, isDayOpen, isLoading: contextLoading } = useDailyRecord()

  // State for category filter
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null)

  // State for quantity selector modal
  const [quantityModalVariant, setQuantityModalVariant] = useState<{
    variant: ProductVariantForSale
    productName: string
  } | null>(null)
  const [quantity, setQuantity] = useState(1)

  // State for void modal
  const [voidModalSale, setVoidModalSale] = useState<RecordedSale | null>(null)
  const [voidReason, setVoidReason] = useState<VoidReason | ''>('')
  const [voidNotes, setVoidNotes] = useState('')

  // Feedback state
  const [feedbackMessage, setFeedbackMessage] = useState<{
    type: 'success' | 'error'
    text: string
  } | null>(null)

  const dailyRecordId = openRecord?.id

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ['salesCategories'],
    queryFn: getCategories,
    enabled: isDayOpen,
  })

  // Fetch products for sale
  const { data: products = [], isLoading: productsLoading } = useQuery({
    queryKey: ['productsForSale', dailyRecordId],
    queryFn: () => getProductsForSale(dailyRecordId!),
    enabled: isDayOpen && !!dailyRecordId,
  })

  // Fetch recent sales
  const { data: recentSales = [], isLoading: recentLoading } = useQuery({
    queryKey: ['recentSales', dailyRecordId],
    queryFn: () => getRecentSales(dailyRecordId!, 10),
    enabled: isDayOpen && !!dailyRecordId,
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  // Fetch day total
  const { data: dayTotal } = useQuery({
    queryKey: ['dayTotal', dailyRecordId],
    queryFn: () => getDayTotal(dailyRecordId!),
    enabled: isDayOpen && !!dailyRecordId,
    refetchInterval: 5000,
  })

  // Record sale mutation
  const recordSaleMutation = useMutation({
    mutationFn: ({ variantId, qty }: { variantId: number; qty: number }) =>
      recordSale(dailyRecordId!, { product_variant_id: variantId, quantity: qty }),
    onSuccess: (sale) => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['productsForSale', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['recentSales', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayTotal', dailyRecordId] })

      // Show success feedback
      const productName = sale.variant_name
        ? `${sale.product_name} ${sale.variant_name}`
        : sale.product_name
      showFeedback('success', t('salesEntry.saleRecordedDesc', {
        product: productName,
        price: formatCurrency(sale.total_pln),
      }))
    },
    onError: () => {
      showFeedback('error', t('salesEntry.errorRecording'))
    },
  })

  // Void sale mutation
  const voidSaleMutation = useMutation({
    mutationFn: ({ saleId, reason, notes }: { saleId: number; reason: VoidReason; notes?: string }) =>
      voidSale(dailyRecordId!, saleId, { reason, notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productsForSale', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['recentSales', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayTotal', dailyRecordId] })
      showFeedback('success', t('salesEntry.voidDialog.success'))
      closeVoidModal()
    },
    onError: () => {
      showFeedback('error', t('salesEntry.voidDialog.error'))
    },
  })

  // Show feedback message
  const showFeedback = useCallback((type: 'success' | 'error', text: string) => {
    setFeedbackMessage({ type, text })
    setTimeout(() => setFeedbackMessage(null), 3000)
  }, [])

  // Filter products by category
  const filteredProducts = useMemo(() => {
    if (!selectedCategoryId) return products
    return products.filter((p) => p.category_id === selectedCategoryId)
  }, [products, selectedCategoryId])

  // Handle product tap - quick add or show quantity selector
  const handleProductTap = useCallback(
    (variant: ProductVariantForSale, _productName: string) => {
      // Quick add 1 item for touch efficiency
      recordSaleMutation.mutate({ variantId: variant.id, qty: 1 })
    },
    [recordSaleMutation]
  )

  // Handle long press to show quantity selector
  const handleProductLongPress = useCallback(
    (variant: ProductVariantForSale, productName: string) => {
      setQuantityModalVariant({ variant, productName })
      setQuantity(1)
    },
    []
  )

  // Handle quantity modal confirm
  const handleQuantityConfirm = useCallback(() => {
    if (quantityModalVariant && quantity > 0) {
      recordSaleMutation.mutate({
        variantId: quantityModalVariant.variant.id,
        qty: quantity,
      })
    }
    setQuantityModalVariant(null)
    setQuantity(1)
  }, [quantityModalVariant, quantity, recordSaleMutation])

  // Open void modal
  const openVoidModal = useCallback((sale: RecordedSale) => {
    setVoidModalSale(sale)
    setVoidReason('')
    setVoidNotes('')
  }, [])

  // Close void modal
  const closeVoidModal = useCallback(() => {
    setVoidModalSale(null)
    setVoidReason('')
    setVoidNotes('')
  }, [])

  // Handle void confirm
  const handleVoidConfirm = useCallback(() => {
    if (voidModalSale && voidReason) {
      voidSaleMutation.mutate({
        saleId: voidModalSale.id,
        reason: voidReason,
        notes: voidNotes || undefined,
      })
    }
  }, [voidModalSale, voidReason, voidNotes, voidSaleMutation])

  // Format time for display
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('pl-PL', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Loading state
  if (contextLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // Day not open state
  if (!isDayOpen || !openRecord) {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-4 bg-gray-50">
        <AlertCircle className="w-16 h-16 text-amber-500 mb-4" />
        <h1 className="text-xl font-semibold text-gray-900 mb-2">
          {t('salesEntry.dayNotOpen')}
        </h1>
        <p className="text-gray-600 mb-6 text-center">
          {t('salesEntry.dayNotOpenDesc')}
        </p>
        <button
          onClick={() => navigate('/operacje')}
          className="btn btn-primary"
        >
          {t('salesEntry.openDayFirst')}
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header - Fixed */}
      <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shadow-sm">
        <button
          onClick={() => navigate(-1)}
          className={`flex items-center gap-2 text-gray-600 hover:text-gray-900 ${TOUCH_TARGET_MIN} px-2`}
          aria-label={t('common.close')}
        >
          <ArrowLeft className="w-6 h-6" />
          <span className="text-lg font-medium">{t('salesEntry.title')}</span>
        </button>

        {/* Day Total */}
        <div className="flex items-center gap-2 bg-primary-50 px-4 py-2 rounded-lg">
          <ShoppingCart className="w-5 h-5 text-primary-600" />
          <div className="text-right">
            <div className="text-xs text-primary-600 font-medium">
              {t('salesEntry.todayTotal')}
            </div>
            <div className="text-lg font-bold text-primary-700">
              {dayTotal ? formatCurrency(dayTotal.total_pln) : '0,00 PLN'}
            </div>
          </div>
        </div>
      </header>

      {/* Category Tabs - Horizontally scrollable */}
      <div className="flex overflow-x-auto bg-white border-b border-gray-200 px-2 py-2 gap-2 scrollbar-hide">
        <button
          onClick={() => setSelectedCategoryId(null)}
          className={`flex-shrink-0 px-4 py-2 rounded-full font-medium transition-colors ${TOUCH_TARGET_MIN} ${
            selectedCategoryId === null
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {t('salesEntry.allCategories')}
        </button>
        {categories.map((category: ProductCategory) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategoryId(category.id)}
            className={`flex-shrink-0 px-4 py-2 rounded-full font-medium transition-colors ${TOUCH_TARGET_MIN} ${
              selectedCategoryId === category.id
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {category.name}
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Product Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          {productsLoading ? (
            <div className="flex items-center justify-center h-full">
              <LoadingSpinner />
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <ShoppingCart className="w-12 h-12 mb-4 opacity-50" />
              <p>{t('salesEntry.noProducts')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {filteredProducts.map((product: ProductForSale) =>
                product.variants.map((variant: ProductVariantForSale) => (
                  <ProductButton
                    key={variant.id}
                    product={product}
                    variant={variant}
                    onTap={handleProductTap}
                    onLongPress={handleProductLongPress}
                    isLoading={recordSaleMutation.isPending}
                    t={t}
                  />
                ))
              )}
            </div>
          )}
        </div>

        {/* Recent Sales Panel - Sidebar on large screens, bottom on small */}
        <div className="lg:w-80 xl:w-96 bg-white border-t lg:border-t-0 lg:border-l border-gray-200 flex flex-col max-h-[300px] lg:max-h-none">
          <div className="px-4 py-3 border-b border-gray-200 flex-shrink-0">
            <h2 className="font-semibold text-gray-900">
              {t('salesEntry.recentSales')}
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {recentLoading ? (
              <div className="p-4">
                <LoadingSpinner size="sm" />
              </div>
            ) : recentSales.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                {t('salesEntry.noRecentSales')}
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {recentSales.map((sale: RecordedSale) => (
                  <li
                    key={sale.id}
                    className={`flex items-center justify-between px-4 py-3 hover:bg-gray-50 ${
                      sale.voided_at ? 'opacity-50 line-through' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {sale.variant_name
                            ? `${sale.product_name} ${sale.variant_name}`
                            : sale.product_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {formatTime(sale.recorded_at)}
                          {sale.quantity > 1 && ` x${sale.quantity}`}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="font-medium text-gray-900">
                        {formatCurrency(sale.total_pln)}
                      </span>
                      {!sale.voided_at && (
                        <button
                          onClick={() => openVoidModal(sale)}
                          className={`text-red-500 hover:text-red-700 p-2 rounded-lg hover:bg-red-50 ${TOUCH_TARGET_MIN}`}
                          title={t('salesEntry.voidSale')}
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Feedback Toast */}
      {feedbackMessage && (
        <div
          className={`fixed bottom-4 left-1/2 -translate-x-1/2 px-6 py-3 rounded-lg shadow-lg z-50 transition-all ${
            feedbackMessage.type === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-red-600 text-white'
          }`}
        >
          {feedbackMessage.text}
        </div>
      )}

      {/* Quantity Selector Modal */}
      {quantityModalVariant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {quantityModalVariant.variant.name
                  ? `${quantityModalVariant.productName} ${quantityModalVariant.variant.name}`
                  : quantityModalVariant.productName}
              </h2>
              <p className="text-sm text-gray-500">
                {formatCurrency(quantityModalVariant.variant.price_pln)} / szt.
              </p>
            </div>
            <div className="p-6">
              <div className="flex items-center justify-center gap-6">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className={`w-14 h-14 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center ${TOUCH_TARGET_MIN}`}
                >
                  <Minus className="w-6 h-6" />
                </button>
                <span className="text-4xl font-bold w-20 text-center">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className={`w-14 h-14 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center ${TOUCH_TARGET_MIN}`}
                >
                  <Plus className="w-6 h-6" />
                </button>
              </div>
              <div className="mt-4 text-center text-lg font-medium text-gray-700">
                {t('common.total')}: {formatCurrency(quantity * quantityModalVariant.variant.price_pln)}
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex gap-3">
              <button
                onClick={() => {
                  setQuantityModalVariant(null)
                  setQuantity(1)
                }}
                className={`flex-1 btn btn-secondary ${TOUCH_TARGET_MIN}`}
              >
                {t('salesEntry.quantitySelector.cancel')}
              </button>
              <button
                onClick={handleQuantityConfirm}
                className={`flex-1 btn btn-primary ${TOUCH_TARGET_MIN}`}
                disabled={recordSaleMutation.isPending}
              >
                {t('salesEntry.quantitySelector.add')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Void Sale Modal */}
      {voidModalSale && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {t('salesEntry.voidDialog.title')}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              {/* Sale Info */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">
                  {t('salesEntry.voidDialog.productLabel')}
                </div>
                <div className="font-medium text-gray-900">
                  {voidModalSale.variant_name
                    ? `${voidModalSale.product_name} ${voidModalSale.variant_name}`
                    : voidModalSale.product_name}
                  {' - '}
                  {formatCurrency(voidModalSale.total_pln)}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {t('salesEntry.voidDialog.recordedAt')}: {formatTime(voidModalSale.recorded_at)}
                </div>
              </div>

              {/* Reason Select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('salesEntry.voidDialog.reasonLabel')} *
                </label>
                <select
                  value={voidReason}
                  onChange={(e) => setVoidReason(e.target.value as VoidReason | '')}
                  className={`input w-full ${TOUCH_TARGET_MIN}`}
                >
                  <option value="">{t('salesEntry.voidDialog.selectReason')}</option>
                  <option value="mistake">{t('salesEntry.voidDialog.reasons.mistake')}</option>
                  <option value="customer_refund">{t('salesEntry.voidDialog.reasons.customer_refund')}</option>
                  <option value="duplicate">{t('salesEntry.voidDialog.reasons.duplicate')}</option>
                  <option value="other">{t('salesEntry.voidDialog.reasons.other')}</option>
                </select>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('salesEntry.voidDialog.notesLabel')}
                </label>
                <textarea
                  value={voidNotes}
                  onChange={(e) => setVoidNotes(e.target.value)}
                  placeholder={t('salesEntry.voidDialog.notesPlaceholder')}
                  className="input w-full h-20 resize-none"
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex gap-3">
              <button
                onClick={closeVoidModal}
                className={`flex-1 btn btn-secondary ${TOUCH_TARGET_MIN}`}
              >
                {t('salesEntry.voidDialog.cancel')}
              </button>
              <button
                onClick={handleVoidConfirm}
                className={`flex-1 btn btn-danger ${TOUCH_TARGET_MIN}`}
                disabled={!voidReason || voidSaleMutation.isPending}
              >
                {voidSaleMutation.isPending
                  ? t('common.processing')
                  : t('salesEntry.voidDialog.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Touch-optimized product button component
 */
interface ProductButtonProps {
  product: ProductForSale
  variant: ProductVariantForSale
  onTap: (variant: ProductVariantForSale, productName: string) => void
  onLongPress: (variant: ProductVariantForSale, productName: string) => void
  isLoading: boolean
  t: ReturnType<typeof useTranslation>['t']
}

function ProductButton({
  product,
  variant,
  onTap,
  onLongPress,
  isLoading,
  t,
}: ProductButtonProps) {
  const [isPressed, setIsPressed] = useState(false)
  const [longPressTimer, setLongPressTimer] = useState<ReturnType<typeof setTimeout> | null>(null)

  const displayName = variant.name
    ? `${product.name} ${variant.name}`
    : product.name

  const handleTouchStart = () => {
    setIsPressed(true)
    const timer = setTimeout(() => {
      onLongPress(variant, product.name)
      setIsPressed(false)
    }, 500) // 500ms for long press
    setLongPressTimer(timer)
  }

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      setLongPressTimer(null)
      // If timer was not triggered, it's a tap
      if (isPressed) {
        onTap(variant, product.name)
      }
    }
    setIsPressed(false)
  }

  const handleTouchCancel = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      setLongPressTimer(null)
    }
    setIsPressed(false)
  }

  return (
    <button
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchCancel}
      onMouseDown={handleTouchStart}
      onMouseUp={handleTouchEnd}
      onMouseLeave={handleTouchCancel}
      disabled={isLoading}
      className={`
        flex flex-col items-center justify-center p-4 rounded-xl
        bg-white border-2 border-gray-200
        transition-all duration-100
        ${isPressed ? 'scale-95 border-primary-400 bg-primary-50' : 'hover:border-primary-300'}
        ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${TOUCH_TARGET_MIN}
        min-h-[100px]
        select-none
        active:scale-95
      `}
    >
      <div className="text-sm font-medium text-gray-900 text-center line-clamp-2">
        {displayName}
      </div>
      <div className="text-lg font-bold text-primary-600 mt-1">
        {formatCurrency(variant.price_pln)}
      </div>
      {variant.today_sold_count > 0 && (
        <div className="text-xs text-gray-500 mt-1">
          ({variant.today_sold_count} {t('salesEntry.soldToday')})
        </div>
      )}
    </button>
  )
}
