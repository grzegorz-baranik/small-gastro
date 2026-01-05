import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  Play,
  Square,
  FileText,
  Truck,
  Package,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Calendar,
  Clock,
} from 'lucide-react'
import { useDailyRecord } from '../context/DailyRecordContext'
import { getRecentDays, getDayEvents } from '../api/dailyOperations'
import { getTodaySales, createSale, deleteSale } from '../api/sales'
import { getProducts } from '../api/products'
import { formatCurrency, formatDate, getTodayDateString } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import {
  OpenDayModal,
  CloseDayModal,
  DaySummary,
  DeliveryModal,
  TransferModal,
  SpoilageModal,
  MidDayEventsList,
} from '../components/daily'
import { ShiftAssignmentSection } from '../components/employees'
import type { DailyRecord, RecentDayRecord } from '../types'

export default function DailyOperationsPage() {
  const { t } = useTranslation()
  const { todayRecord, isDayOpen, isLoading: recordLoading, refetch } = useDailyRecord()
  const queryClient = useQueryClient()

  // Modal states
  const [openDayModalOpen, setOpenDayModalOpen] = useState(false)
  const [closeDayModalOpen, setCloseDayModalOpen] = useState(false)
  const [summaryModalOpen, setSummaryModalOpen] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<DailyRecord | null>(null)

  // Mid-day operation modal states
  const [deliveryModalOpen, setDeliveryModalOpen] = useState(false)
  const [transferModalOpen, setTransferModalOpen] = useState(false)
  const [spoilageModalOpen, setSpoilageModalOpen] = useState(false)

  // Fetch recent days
  const { data: recentDays, isLoading: recentDaysLoading } = useQuery({
    queryKey: ['recentDays'],
    queryFn: () => getRecentDays(7),
  })

  // Fetch today's sales
  const { data: salesData, isLoading: salesLoading } = useQuery({
    queryKey: ['todaySales'],
    queryFn: getTodaySales,
    enabled: isDayOpen,
  })

  // Fetch day events for today
  const { data: dayEvents } = useQuery({
    queryKey: ['dayEvents', todayRecord?.id],
    queryFn: () => getDayEvents(todayRecord!.id),
    enabled: isDayOpen && !!todayRecord?.id,
  })

  // Fetch products
  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: () => getProducts(true),
    enabled: isDayOpen,
  })

  // Create sale mutation
  const createSaleMutation = useMutation({
    mutationFn: createSale,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['todaySales'] }),
  })

  // Delete sale mutation
  const deleteSaleMutation = useMutation({
    mutationFn: deleteSale,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['todaySales'] }),
  })

  // Get day of week name
  const getDayName = (dateString: string): string => {
    const date = new Date(dateString)
    const dayKeys = [
      'sunday',
      'monday',
      'tuesday',
      'wednesday',
      'thursday',
      'friday',
      'saturday',
    ]
    return t(`dailyOperations.dayOfWeek.${dayKeys[date.getDay()]}`)
  }

  // Get status badge
  const getStatusBadge = (status: string) => {
    if (status === 'open') {
      return (
        <span className="px-3 py-1 text-sm font-medium bg-green-100 text-green-800 rounded-full">
          {t('dailyOperations.statusOpen')}
        </span>
      )
    }
    return (
      <span className="px-3 py-1 text-sm font-medium bg-gray-100 text-gray-800 rounded-full">
        {t('dailyOperations.statusClosed')}
      </span>
    )
  }

  // Handle opening day summary
  const handleOpenSummary = (record: DailyRecord) => {
    setSelectedRecord(record)
    setSummaryModalOpen(true)
  }

  // Handle success callbacks
  const handleOpenDaySuccess = () => {
    refetch()
    queryClient.invalidateQueries({ queryKey: ['recentDays'] })
  }

  const handleCloseDaySuccess = () => {
    refetch()
    queryClient.invalidateQueries({ queryKey: ['recentDays'] })
    queryClient.invalidateQueries({ queryKey: ['todaySales'] })
  }

  // Handle mid-day operation success - just invalidate day events
  const handleMidDayOperationSuccess = () => {
    if (todayRecord) {
      queryClient.invalidateQueries({ queryKey: ['dayEvents', todayRecord.id] })
    }
  }

  if (recordLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  const today = getTodayDateString()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('dailyOperations.title')}</h1>
      </div>

      {/* Today's status card */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Calendar className="w-8 h-8 text-primary-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {t('dailyOperations.todayLabel')} {formatDate(today)} ({getDayName(today)})
              </h2>
              {todayRecord?.opened_at && (
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {t('dailyOperations.openedAt')} {new Date(todayRecord.opened_at).toLocaleTimeString('pl-PL', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              )}
            </div>
          </div>
          <div>
            {todayRecord ? getStatusBadge(todayRecord.status) : (
              <span className="px-3 py-1 text-sm font-medium bg-yellow-100 text-yellow-800 rounded-full">
                {t('dailyOperations.statusNotOpened')}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={() => setOpenDayModalOpen(true)}
            disabled={isDayOpen}
            className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
              isDayOpen
                ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                : 'border-primary-200 bg-primary-50 text-primary-700 hover:bg-primary-100 hover:border-primary-300'
            }`}
          >
            <Play className="w-8 h-8" />
            <span className="font-medium">{t('dailyOperations.openDay')}</span>
          </button>

          <button
            onClick={() => {
              if (todayRecord) {
                setCloseDayModalOpen(true)
              }
            }}
            disabled={!isDayOpen}
            className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
              !isDayOpen
                ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                : 'border-orange-200 bg-orange-50 text-orange-700 hover:bg-orange-100 hover:border-orange-300'
            }`}
          >
            <Square className="w-8 h-8" />
            <span className="font-medium">{t('dailyOperations.closeDay')}</span>
          </button>

          <button
            onClick={() => {
              if (todayRecord) {
                handleOpenSummary(todayRecord)
              }
            }}
            disabled={!todayRecord}
            className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
              !todayRecord
                ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                : 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300'
            }`}
          >
            <FileText className="w-8 h-8" />
            <span className="font-medium">{t('dailyOperations.summary')}</span>
          </button>
        </div>
      </div>

      {/* Mid-day operations buttons - only show when day is open */}
      {isDayOpen && todayRecord && (
        <div className="card">
          <h3 className="card-header">{t('dailyOperations.storageOperations')}</h3>
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => setDeliveryModalOpen(true)}
              className="p-4 rounded-lg border-2 border-green-200 bg-green-50 text-green-700 hover:bg-green-100 hover:border-green-300 transition-colors flex flex-col items-center gap-2"
            >
              <Truck className="w-8 h-8" />
              <span className="font-medium">{t('dailyOperations.addDelivery')}</span>
            </button>
            <button
              onClick={() => setTransferModalOpen(true)}
              className="p-4 rounded-lg border-2 border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300 transition-colors flex flex-col items-center gap-2"
            >
              <Package className="w-8 h-8" />
              <span className="font-medium">{t('dailyOperations.transferFromStorage')}</span>
            </button>
            <button
              onClick={() => setSpoilageModalOpen(true)}
              className="p-4 rounded-lg border-2 border-red-200 bg-red-50 text-red-700 hover:bg-red-100 hover:border-red-300 transition-colors flex flex-col items-center gap-2"
            >
              <Trash2 className="w-8 h-8" />
              <span className="font-medium">{t('dailyOperations.recordSpoilage')}</span>
            </button>
          </div>
        </div>
      )}

      {/* Today's events summary - only show when day is open */}
      {isDayOpen && dayEvents && (
        <div className="card">
          <h3 className="card-header">{t('dailyOperations.eventSummary')}</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <Truck className="w-6 h-6 text-green-600" />
              <div>
                <p className="text-sm text-green-600">{t('dailyOperations.deliveries')}</p>
                <p className="font-semibold text-green-800">
                  {dayEvents.deliveries_count} {t('common.items')}
                </p>
                <p className="text-sm text-green-600">
                  {formatCurrency(dayEvents.deliveries_total_pln)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
              <Package className="w-6 h-6 text-blue-600" />
              <div>
                <p className="text-sm text-blue-600">{t('dailyOperations.transfers')}</p>
                <p className="font-semibold text-blue-800">
                  {dayEvents.transfers_count} {t('common.items')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg">
              <Trash2 className="w-6 h-6 text-red-600" />
              <div>
                <p className="text-sm text-red-600">{t('dailyOperations.spoilage')}</p>
                <p className="font-semibold text-red-800">
                  {dayEvents.spoilage_count} {t('common.items')}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mid-day events list - only show when day is open */}
      {isDayOpen && todayRecord && (
        <MidDayEventsList dailyRecordId={todayRecord.id} />
      )}

      {/* Shift assignments - only show when day is open or today's record exists */}
      {todayRecord && (
        <ShiftAssignmentSection
          dailyRecordId={todayRecord.id}
          isEditable={isDayOpen}
        />
      )}

      {/* Sales section - only show when day is open */}
      {isDayOpen && (
        <>
          {/* Quick sales entry */}
          <div className="card">
            <h3 className="card-header">{t('dailyOperations.addSale')}</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {productsData?.items.map((product) => (
                <button
                  key={product.id}
                  onClick={() =>
                    createSaleMutation.mutate({
                      product_id: product.id,
                      quantity_sold: 1,
                    })
                  }
                  disabled={createSaleMutation.isPending}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-left"
                >
                  <p className="font-medium text-gray-900">{product.name}</p>
                  <p className="text-primary-600 font-bold">
                    {formatCurrency(product.variants[0]?.price_pln ?? 0)}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Today's sales list */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="card-header mb-0">{t('dailyOperations.todaySales')}</h3>
              <div className="text-right">
                <p className="text-sm text-gray-500">{t('common.sum')}</p>
                <p className="text-xl font-bold text-primary-600">
                  {formatCurrency(salesData?.total_revenue ?? 0)}
                </p>
              </div>
            </div>

            {salesLoading ? (
              <LoadingSpinner />
            ) : salesData?.items.length === 0 ? (
              <p className="text-gray-500 text-center py-8">{t('dailyOperations.noSales')}</p>
            ) : (
              <div className="space-y-2">
                {salesData?.items.map((sale) => (
                  <div
                    key={sale.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900">
                        {sale.product_name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {sale.quantity_sold} x {formatCurrency(sale.unit_price)}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <p className="font-bold text-gray-900">
                        {formatCurrency(sale.total_price)}
                      </p>
                      <button
                        onClick={() => deleteSaleMutation.mutate(sale.id)}
                        className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Recent days history */}
      <div className="card">
        <h3 className="card-header">{t('dailyOperations.recentDays')}</h3>
        {recentDaysLoading ? (
          <LoadingSpinner />
        ) : recentDays && recentDays.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                    {t('common.date')}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                    {t('common.status')}
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                    {t('dailyOperations.income')}
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">
                    {t('dailyOperations.alerts')}
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                    {t('common.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recentDays.map((day: RecentDayRecord) => (
                  <tr key={day.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">
                        {formatDate(day.date)}
                      </div>
                      <div className="text-sm text-gray-500">
                        {getDayName(day.date)}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {day.status === 'open' ? (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                          <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5"></span>
                          {t('dailyOperations.statusOpen')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                          {t('dailyOperations.statusClosed')}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      {day.total_income_pln !== null
                        ? formatCurrency(day.total_income_pln)
                        : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {day.alerts_count > 0 ? (
                        <span className="inline-flex items-center gap-1 text-yellow-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm">
                            {day.alerts_count} {day.alerts_count === 1 ? t('dailyOperations.warningCount') : t('dailyOperations.warningsCount')}
                          </span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-green-600">
                          <CheckCircle className="w-4 h-4" />
                          <span className="text-sm">{t('common.ok')}</span>
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() =>
                          handleOpenSummary({
                            id: day.id,
                            date: day.date,
                            status: day.status,
                            opened_at: day.opened_at || '',
                            closed_at: day.closed_at,
                            notes: null,
                            total_income_pln: day.total_income_pln,
                            total_delivery_cost_pln: null,
                            total_spoilage_cost_pln: null,
                            created_at: '',
                            updated_at: null,
                          })
                        }
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        {t('common.viewDetails')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">{t('dailyOperations.noHistory')}</p>
        )}
      </div>

      {/* Modals */}
      <OpenDayModal
        isOpen={openDayModalOpen}
        onClose={() => setOpenDayModalOpen(false)}
        onSuccess={handleOpenDaySuccess}
      />

      {todayRecord && (
        <CloseDayModal
          isOpen={closeDayModalOpen}
          onClose={() => setCloseDayModalOpen(false)}
          onSuccess={handleCloseDaySuccess}
          dailyRecord={todayRecord}
        />
      )}

      {selectedRecord && (
        <DaySummary
          isOpen={summaryModalOpen}
          onClose={() => {
            setSummaryModalOpen(false)
            setSelectedRecord(null)
          }}
          dailyRecord={selectedRecord}
        />
      )}

      {/* Mid-day operation modals */}
      {todayRecord && (
        <>
          <DeliveryModal
            isOpen={deliveryModalOpen}
            onClose={() => setDeliveryModalOpen(false)}
            onSuccess={handleMidDayOperationSuccess}
            dailyRecordId={todayRecord.id}
          />
          <TransferModal
            isOpen={transferModalOpen}
            onClose={() => setTransferModalOpen(false)}
            onSuccess={handleMidDayOperationSuccess}
            dailyRecordId={todayRecord.id}
          />
          <SpoilageModal
            isOpen={spoilageModalOpen}
            onClose={() => setSpoilageModalOpen(false)}
            onSuccess={handleMidDayOperationSuccess}
            dailyRecordId={todayRecord.id}
          />
        </>
      )}
    </div>
  )
}
