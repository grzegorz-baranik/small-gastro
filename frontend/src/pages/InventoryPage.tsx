import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Warehouse, Store, AlertTriangle, RefreshCw, Package } from 'lucide-react'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { BatchExpiryPanel, StockLevelsTable, StockAdjustmentModal, QuickTransferModal } from '../components/inventory'
import { getStockLevels, createStockAdjustment } from '../api/inventory'
import { createTransfer } from '../api/midDayOperations'
import { useDailyRecord } from '../context/DailyRecordContext'
import { useToast } from '../context/ToastContext'
import type { StockAdjustmentCreate } from '../types'

type TabType = 'stockLevels' | 'batches'

export default function InventoryPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const { openRecord } = useDailyRecord()

  const [activeTab, setActiveTab] = useState<TabType>('stockLevels')

  // Adjustment modal state
  const [adjustmentModal, setAdjustmentModal] = useState<{
    isOpen: boolean
    ingredientId: number | null
    ingredientName: string
    location: 'storage' | 'shop'
    currentQuantity: number
    unitLabel: string
  }>({
    isOpen: false,
    ingredientId: null,
    ingredientName: '',
    location: 'storage',
    currentQuantity: 0,
    unitLabel: 'szt',
  })

  // Transfer modal state
  const [transferModal, setTransferModal] = useState<{
    isOpen: boolean
    ingredientId: number | null
    ingredientName: string
    warehouseQuantity: number
    unitLabel: string
  }>({
    isOpen: false,
    ingredientId: null,
    ingredientName: '',
    warehouseQuantity: 0,
    unitLabel: 'szt',
  })

  // Fetch stock levels
  const { data: stockLevels = [], isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['stockLevels'],
    queryFn: getStockLevels,
    staleTime: 30000, // 30 seconds
  })

  // Create adjustment mutation
  const adjustmentMutation = useMutation({
    mutationFn: createStockAdjustment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockLevels'] })
      showToast(t('inventory.adjustment.success'), 'success')
    },
    onError: () => {
      showToast(t('inventory.adjustment.error'), 'error')
    },
  })

  // Create transfer mutation
  const transferMutation = useMutation({
    mutationFn: async ({ ingredientId, quantity }: { ingredientId: number; quantity: number }) => {
      if (!openRecord?.id) {
        throw new Error('No open day')
      }
      return createTransfer({
        daily_record_id: openRecord.id,
        ingredient_id: ingredientId,
        quantity,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockLevels'] })
      showToast(t('inventory.transfer.success'), 'success')
    },
    onError: () => {
      showToast(t('inventory.transfer.error'), 'error')
    },
  })

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    const warehouseItems = stockLevels.filter(s => s.warehouse_qty > 0).length
    const shopItems = stockLevels.filter(s => s.shop_qty > 0).length
    const expiryAlerts = stockLevels.filter(s => {
      if (!s.nearest_expiry) return false
      const daysUntilExpiry = Math.ceil(
        (new Date(s.nearest_expiry).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      )
      return daysUntilExpiry <= 7
    }).length

    return { warehouseItems, shopItems, expiryAlerts }
  }, [stockLevels])

  // Handle adjustment click
  const handleAdjust = (ingredientId: number, location: 'storage' | 'shop') => {
    const stockItem = stockLevels.find(s => s.ingredient_id === ingredientId)
    if (!stockItem) return

    setAdjustmentModal({
      isOpen: true,
      ingredientId,
      ingredientName: stockItem.ingredient_name,
      location,
      currentQuantity: location === 'storage' ? stockItem.warehouse_qty : stockItem.shop_qty,
      unitLabel: stockItem.unit_label,
    })
  }

  // Handle transfer click
  const handleTransfer = (ingredientId: number) => {
    const stockItem = stockLevels.find(s => s.ingredient_id === ingredientId)
    if (!stockItem) return

    setTransferModal({
      isOpen: true,
      ingredientId,
      ingredientName: stockItem.ingredient_name,
      warehouseQuantity: stockItem.warehouse_qty,
      unitLabel: stockItem.unit_label,
    })
  }

  // Handle adjustment submit
  const handleAdjustmentSubmit = async (data: StockAdjustmentCreate) => {
    await adjustmentMutation.mutateAsync(data)
  }

  // Handle transfer submit
  const handleTransferSubmit = async (quantity: number) => {
    if (!transferModal.ingredientId) return
    await transferMutation.mutateAsync({
      ingredientId: transferModal.ingredientId,
      quantity,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('inventory.title')}</h1>
        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="btn btn-secondary flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
          {t('inventory.actions.refresh')}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Warehouse className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">{t('inventory.summary.warehouseItems')}</p>
              <p className="text-2xl font-bold text-gray-900">{summaryStats.warehouseItems}</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Store className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">{t('inventory.summary.shopItems')}</p>
              <p className="text-2xl font-bold text-gray-900">{summaryStats.shopItems}</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${summaryStats.expiryAlerts > 0 ? 'bg-yellow-100' : 'bg-gray-100'}`}>
              <AlertTriangle className={`w-5 h-5 ${summaryStats.expiryAlerts > 0 ? 'text-yellow-600' : 'text-gray-400'}`} />
            </div>
            <div>
              <p className="text-sm text-gray-500">{t('inventory.summary.expiryAlerts')}</p>
              <p className={`text-2xl font-bold ${summaryStats.expiryAlerts > 0 ? 'text-yellow-600' : 'text-gray-900'}`}>
                {summaryStats.expiryAlerts}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex gap-4" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('stockLevels')}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'stockLevels'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            aria-current={activeTab === 'stockLevels' ? 'page' : undefined}
          >
            <Warehouse className="w-4 h-4" />
            {t('inventory.tabs.stockLevels')}
          </button>
          <button
            onClick={() => setActiveTab('batches')}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'batches'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            aria-current={activeTab === 'batches' ? 'page' : undefined}
            data-testid="batches-tab"
          >
            <Package className="w-4 h-4" />
            {t('inventory.tabs.batches')}
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'stockLevels' ? (
        <div className="card">
          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <StockLevelsTable
              stockLevels={stockLevels}
              isLoading={isLoading}
              onAdjust={handleAdjust}
              onTransfer={handleTransfer}
            />
          )}
        </div>
      ) : (
        <div className="card" data-testid="batch-tracking-panel">
          <h2 className="card-header flex items-center gap-2">
            <Package className="w-5 h-5" />
            {t('batch.title')}
          </h2>
          <BatchExpiryPanel />
        </div>
      )}

      {/* Modals */}
      <StockAdjustmentModal
        isOpen={adjustmentModal.isOpen}
        onClose={() => setAdjustmentModal(prev => ({ ...prev, isOpen: false }))}
        ingredientId={adjustmentModal.ingredientId}
        ingredientName={adjustmentModal.ingredientName}
        location={adjustmentModal.location}
        currentQuantity={adjustmentModal.currentQuantity}
        unitLabel={adjustmentModal.unitLabel}
        onSubmit={handleAdjustmentSubmit}
      />

      <QuickTransferModal
        isOpen={transferModal.isOpen}
        onClose={() => setTransferModal(prev => ({ ...prev, isOpen: false }))}
        ingredientId={transferModal.ingredientId}
        ingredientName={transferModal.ingredientName}
        warehouseQuantity={transferModal.warehouseQuantity}
        unitLabel={transferModal.unitLabel}
        onSubmit={handleTransferSubmit}
      />
    </div>
  )
}
