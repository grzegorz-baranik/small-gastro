import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  Calendar,
  Clock,
  Truck,
  Package,
  Trash2,
  DollarSign,
  AlertCircle,
} from 'lucide-react'
import LoadingSpinner from '../../common/LoadingSpinner'
import { getDaySummary, getDayEvents } from '../../../api/dailyOperations'
import { formatCurrency, formatDate, formatDateTime } from '../../../utils/formatters'
import type { DayStatus } from '../../../types'

interface DayOverviewSectionProps {
  dayId: number
}

export default function DayOverviewSection({ dayId }: DayOverviewSectionProps) {
  const { t } = useTranslation()

  // Fetch day summary
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({
    queryKey: ['daySummary', dayId],
    queryFn: () => getDaySummary(dayId),
    enabled: !!dayId,
  })

  // Fetch day events
  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ['dayEvents', dayId],
    queryFn: () => getDayEvents(dayId),
    enabled: !!dayId,
  })

  const isLoading = summaryLoading || eventsLoading

  // Get status badge styling
  const getStatusBadge = (status: DayStatus) => {
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

  // Get Polish day name
  const getDayName = (dateString: string): string => {
    const date = new Date(dateString)
    const dayNames = [
      t('dailyOperations.dayOfWeek.sunday'),
      t('dailyOperations.dayOfWeek.monday'),
      t('dailyOperations.dayOfWeek.tuesday'),
      t('dailyOperations.dayOfWeek.wednesday'),
      t('dailyOperations.dayOfWeek.thursday'),
      t('dailyOperations.dayOfWeek.friday'),
      t('dailyOperations.dayOfWeek.saturday'),
    ]
    return dayNames[date.getDay()]
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    )
  }

  if (summaryError) {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
        <p className="text-red-800">{t('errors.generic')}</p>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="text-center py-12 text-gray-500">
        {t('common.noData')}
      </div>
    )
  }

  const { daily_record } = summary

  return (
    <div className="space-y-6">
      {/* Header with date and status */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-3">
          <Calendar className="w-6 h-6 text-primary-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {formatDate(daily_record.date)}
            </h3>
            <p className="text-sm text-gray-500">
              {getDayName(daily_record.date)}
            </p>
          </div>
        </div>
        {getStatusBadge(daily_record.status)}
      </div>

      {/* Time information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-lg">
          <Clock className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              {t('wizard.openedAt')}
            </p>
            <p className="font-medium text-gray-900">
              {summary.opening_time ? formatDateTime(summary.opening_time) : '-'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-lg">
          <Clock className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              {t('closeDayModal.closing')}
            </p>
            <p className="font-medium text-gray-900">
              {summary.closing_time ? formatDateTime(summary.closing_time) : '-'}
            </p>
          </div>
        </div>
      </div>

      {/* Events summary */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          {t('daySummary.dayEvents')}
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Deliveries */}
          <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
            <Truck className="w-5 h-5 text-green-600" />
            <div>
              <p className="text-xs text-green-600 uppercase tracking-wide">
                {t('dailyOperations.deliveries')}
              </p>
              <p className="font-semibold text-green-800">
                {events?.deliveries_count ?? summary.events.deliveries_count} {t('common.items')}
              </p>
              <p className="text-sm text-green-600">
                {formatCurrency(events?.deliveries_total_pln ?? summary.events.deliveries_total_pln)}
              </p>
            </div>
          </div>

          {/* Transfers */}
          <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <Package className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-xs text-blue-600 uppercase tracking-wide">
                {t('dailyOperations.transfers')}
              </p>
              <p className="font-semibold text-blue-800">
                {events?.transfers_count ?? summary.events.transfers_count} {t('common.items')}
              </p>
            </div>
          </div>

          {/* Spoilage */}
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <Trash2 className="w-5 h-5 text-red-600" />
            <div>
              <p className="text-xs text-red-600 uppercase tracking-wide">
                {t('dailyOperations.spoilage')}
              </p>
              <p className="font-semibold text-red-800">
                {events?.spoilage_count ?? summary.events.spoilage_count} {t('common.items')}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Financial summary */}
      <div className="p-4 bg-primary-50 border border-primary-200 rounded-lg">
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="w-5 h-5 text-primary-600" />
          <h4 className="text-sm font-medium text-primary-800">
            {t('wizard.financialSummary')}
          </h4>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-primary-600 uppercase tracking-wide">
              {t('wizard.revenue')}
            </p>
            <p className="text-xl font-bold text-primary-900">
              {formatCurrency(summary.total_income_pln)}
            </p>
          </div>
          <div>
            <p className="text-xs text-primary-600 uppercase tracking-wide">
              {t('wizard.deliveryCosts')}
            </p>
            <p className="text-xl font-bold text-primary-900">
              {formatCurrency(summary.events.deliveries_total_pln)}
            </p>
          </div>
          <div>
            <p className="text-xs text-primary-600 uppercase tracking-wide">
              {t('wizard.grossProfit')}
            </p>
            <p className="text-xl font-bold text-primary-900">
              {formatCurrency(summary.total_income_pln - summary.events.deliveries_total_pln)}
            </p>
          </div>
        </div>
      </div>

      {/* Sales info (if any) */}
      {summary.calculated_sales.length > 0 && (
        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            {t('closeDayModal.calculatedSales')}
          </h4>
          <div className="text-sm text-gray-600">
            {summary.calculated_sales.length} {t('common.items')} - {formatCurrency(summary.total_income_pln)}
          </div>
        </div>
      )}

      {/* Discrepancy alerts */}
      {summary.discrepancy_alerts.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            {t('dailyOperations.alerts')}
          </h4>
          <div className="space-y-2">
            {summary.discrepancy_alerts.map((alert) => {
              const colorClass =
                alert.level === 'critical'
                  ? 'bg-red-50 border-red-200 text-red-800'
                  : alert.level === 'warning'
                  ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                  : 'bg-green-50 border-green-200 text-green-800'
              return (
                <div
                  key={alert.ingredient_id}
                  className={`flex items-center gap-2 p-3 rounded-lg border ${colorClass}`}
                >
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm font-medium">{alert.message}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Notes */}
      {daily_record.notes && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            {t('wizard.notes')}
          </h4>
          <p className="text-gray-600">{daily_record.notes}</p>
        </div>
      )}
    </div>
  )
}
