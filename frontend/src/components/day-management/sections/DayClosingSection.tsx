import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  Copy,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Loader2,
  Lock,
  FileText,
} from 'lucide-react'
import {
  getDaySummary,
  closeDay,
  getPreviousClosing,
} from '../../../api/dailyOperations'
import { getDeliveries } from '../../../api/midDayOperations'
import { useClosingCalculations } from '../../../hooks/useClosingCalculations'
import { formatQuantity, formatCurrency, formatDate } from '../../../utils/formatters'
import LoadingSpinner from '../../common/LoadingSpinner'
import type { CalculatedRow } from '../../../hooks/useClosingCalculations'
import type { DeliverySummaryItem } from '../../../types'

interface DayClosingSectionProps {
  dayId: number
  isEditable: boolean
  onDayClosed?: () => void
}

export default function DayClosingSection({
  dayId,
  isEditable,
  onDayClosed,
}: DayClosingSectionProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  // Form state
  const [closingInventory, setClosingInventory] = useState<Record<number, string>>({})
  const [notes, setNotes] = useState('')

  // Fetch day summary
  const {
    data: daySummary,
    isLoading: isSummaryLoading,
  } = useQuery({
    queryKey: ['daySummary', dayId],
    queryFn: () => getDaySummary(dayId),
    enabled: !!dayId,
    staleTime: 30000,
  })

  // Fetch previous closing for comparison (only for open days)
  // Note: previousClosingData could be used in the future for comparison display
  useQuery({
    queryKey: ['previousClosing'],
    queryFn: getPreviousClosing,
    enabled: isEditable,
    staleTime: 60000,
  })

  // Fetch deliveries
  const { data: deliveries = [] } = useQuery({
    queryKey: ['deliveries', dayId],
    queryFn: () => getDeliveries(dayId),
    enabled: !!dayId,
    staleTime: 30000,
  })


  // Flatten deliveries (they have nested items)
  const flattenedDeliveries: DeliverySummaryItem[] = useMemo(() => {
    return deliveries.flatMap((delivery) =>
      delivery.items.map((item) => ({
        id: item.id,
        ingredient_id: item.ingredient_id,
        ingredient_name: item.ingredient_name,
        unit_label: item.unit_label,
        quantity: item.quantity,
        price_pln: item.cost_pln ?? delivery.total_cost_pln / delivery.items.length,
        delivered_at: delivery.delivered_at,
      }))
    )
  }, [deliveries])

  // Real-time calculations (only for editable mode)
  const { rows, alerts, isValid } = useClosingCalculations({
    usageItems: daySummary?.usage_items || [],
    closingInventory,
  })

  // Close day mutation
  const closeMutation = useMutation({
    mutationFn: () =>
      closeDay(
        dayId,
        rows.map((r) => ({
          ingredient_id: r.ingredientId,
          quantity: r.closing!,
        })),
        notes || undefined
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daySummary'] })
      queryClient.invalidateQueries({ queryKey: ['dailyRecord'] })
      queryClient.invalidateQueries({ queryKey: ['openRecord'] })
      queryClient.invalidateQueries({ queryKey: ['todayRecord'] })
      queryClient.invalidateQueries({ queryKey: ['recentDays'] })
      onDayClosed?.()
    },
  })

  // Handle input change for closing inventory
  const handleInputChange = (ingredientId: number, value: string) => {
    setClosingInventory((prev) => ({
      ...prev,
      [ingredientId]: value,
    }))
  }

  // Copy expected values to closing
  const handleCopyExpected = () => {
    const newInventory: Record<number, string> = {}
    rows.forEach((row) => {
      newInventory[row.ingredientId] = row.expected.toString()
    })
    setClosingInventory(newInventory)
  }

  // Handle close day
  const handleCloseDay = () => {
    closeMutation.mutate()
  }

  // Get status badge for a row
  const getStatusBadge = (row: CalculatedRow) => {
    if (row.closing === null) return null
    if (!row.discrepancyLevel) return null

    const config = {
      ok: {
        bg: 'bg-green-100 text-green-800 border-green-200',
        icon: <CheckCircle className="w-3.5 h-3.5" />,
        label: 'OK',
      },
      warning: {
        bg: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        icon: <AlertTriangle className="w-3.5 h-3.5" />,
        label: `${row.discrepancyPercent?.toFixed(0)}%`,
      },
      critical: {
        bg: 'bg-red-100 text-red-800 border-red-200',
        icon: <AlertCircle className="w-3.5 h-3.5" />,
        label: `${row.discrepancyPercent?.toFixed(0)}%`,
      },
    }

    const { bg, icon, label } = config[row.discrepancyLevel]

    return (
      <div
        className={`flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${bg}`}
      >
        {icon}
        <span>{label}</span>
      </div>
    )
  }

  // Separate alerts by level
  const warningAlerts = alerts.filter((a) => a.level === 'warning')
  const criticalAlerts = alerts.filter((a) => a.level === 'critical')

  // Calculate financial summary
  const totalDeliveryCost = flattenedDeliveries.reduce(
    (sum, d) => sum + (d.price_pln ?? 0),
    0
  )

  if (isSummaryLoading) {
    return (
      <div className="card">
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  // Closed day - read-only view
  if (!isEditable) {
    return (
      <div className="space-y-6">
        {/* Closed indicator */}
        <div className="card bg-gray-50 border-gray-200">
          <div className="flex items-center gap-3">
            <Lock className="w-6 h-6 text-gray-400" />
            <div>
              <h3 className="font-medium text-gray-700">
                {t('dailyOperations.statusClosed')}
              </h3>
              <p className="text-sm text-gray-500">
                {daySummary?.closing_time
                  ? `${t('wizard.closingSummary')}: ${formatDate(daySummary.closing_time)}`
                  : t('wizard.closingSummary')}
              </p>
            </div>
          </div>
        </div>

        {/* Closing inventory (read-only) */}
        <div className="card">
          <h3 className="card-header">{t('wizard.closingInventory')}</h3>
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('menu.ingredient')}
                    </th>
                    <th className="px-3 py-2.5 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('wizard.openingShort')}
                    </th>
                    <th className="px-3 py-2.5 text-right text-xs font-medium text-green-600 uppercase tracking-wider">
                      +{t('wizard.deliveriesShort')}
                    </th>
                    <th className="px-3 py-2.5 text-right text-xs font-medium text-blue-600 uppercase tracking-wider">
                      +{t('wizard.transfersShort')}
                    </th>
                    <th className="px-3 py-2.5 text-right text-xs font-medium text-red-600 uppercase tracking-wider">
                      -{t('wizard.spoilageShort')}
                    </th>
                    <th className="px-3 py-2.5 text-right text-xs font-medium text-gray-700 uppercase tracking-wider bg-gray-100">
                      {t('wizard.closingShort')}
                    </th>
                    <th className="px-3 py-2.5 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                      {t('wizard.usageShort')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {daySummary?.usage_items.map((item) => (
                    <tr key={item.ingredient_id}>
                      <td className="px-3 py-2.5">
                        <div className="font-medium text-gray-900">
                          {item.ingredient_name}
                        </div>
                        <div className="text-xs text-gray-500">{item.unit_label}</div>
                      </td>
                      <td className="px-3 py-2.5 text-right text-gray-600">
                        {formatQuantity(item.opening_quantity, item.unit_type, item.unit_label)}
                      </td>
                      <td className="px-3 py-2.5 text-right text-green-600">
                        {item.deliveries_quantity > 0
                          ? `+${formatQuantity(item.deliveries_quantity, item.unit_type, item.unit_label)}`
                          : '-'}
                      </td>
                      <td className="px-3 py-2.5 text-right text-blue-600">
                        {item.transfers_quantity > 0
                          ? `+${formatQuantity(item.transfers_quantity, item.unit_type, item.unit_label)}`
                          : '-'}
                      </td>
                      <td className="px-3 py-2.5 text-right text-red-600">
                        {item.spoilage_quantity > 0
                          ? `-${formatQuantity(item.spoilage_quantity, item.unit_type, item.unit_label)}`
                          : '-'}
                      </td>
                      <td className="px-3 py-2.5 text-right font-bold text-gray-900 bg-gray-50">
                        {item.closing_quantity !== null
                          ? formatQuantity(item.closing_quantity, item.unit_type, item.unit_label)
                          : '-'}
                      </td>
                      <td className="px-3 py-2.5 text-right font-medium">
                        {item.usage !== null ? (
                          <span className="text-orange-600">
                            {formatQuantity(item.usage, item.unit_type, item.unit_label)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Financial summary */}
        <div className="card">
          <h3 className="card-header">{t('wizard.financialSummary')}</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600">{t('wizard.revenue')}</p>
              <p className="text-xl font-bold text-green-800">
                {formatCurrency(daySummary?.total_income_pln ?? 0)}
              </p>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <p className="text-sm text-red-600">{t('wizard.deliveryCosts')}</p>
              <p className="text-xl font-bold text-red-800">
                {formatCurrency(totalDeliveryCost)}
              </p>
            </div>
            <div className="p-4 bg-primary-50 rounded-lg">
              <p className="text-sm text-primary-600">{t('wizard.grossProfit')}</p>
              <p className="text-xl font-bold text-primary-800">
                {formatCurrency((daySummary?.total_income_pln ?? 0) - totalDeliveryCost)}
              </p>
            </div>
          </div>
        </div>

        {/* Notes */}
        {daySummary?.daily_record.notes && (
          <div className="card">
            <h3 className="card-header">{t('wizard.notes')}</h3>
            <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
              <FileText className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
              <p className="text-gray-700">{daySummary.daily_record.notes}</p>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Editable mode - closing form
  return (
    <div className="space-y-6">
      {/* Formula explanation and copy button */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-gray-700">
              {t('wizard.formula')}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {t('wizard.enterClosingHint')}
            </p>
          </div>
          <button
            type="button"
            onClick={handleCopyExpected}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
          >
            <Copy className="w-4 h-4" />
            {t('wizard.copyExpected')}
          </button>
        </div>
      </div>

      {/* Closing inventory form table */}
      <div className="card">
        <h3 className="card-header">{t('wizard.closingInventory')}</h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('menu.ingredient')}
                  </th>
                  <th className="px-3 py-2.5 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('wizard.openingShort')}
                  </th>
                  <th className="px-3 py-2.5 text-right text-xs font-medium text-green-600 uppercase tracking-wider">
                    +{t('wizard.deliveriesShort')}
                  </th>
                  <th className="px-3 py-2.5 text-right text-xs font-medium text-blue-600 uppercase tracking-wider">
                    +{t('wizard.transfersShort')}
                  </th>
                  <th className="px-3 py-2.5 text-right text-xs font-medium text-red-600 uppercase tracking-wider">
                    -{t('wizard.spoilageShort')}
                  </th>
                  <th className="px-3 py-2.5 text-right text-xs font-medium text-gray-700 uppercase tracking-wider bg-gray-100">
                    ={t('wizard.expectedShort')}
                  </th>
                  <th className="px-3 py-2.5 text-center text-xs font-medium text-primary-600 uppercase tracking-wider bg-primary-50">
                    {t('wizard.closingShort')}
                  </th>
                  <th className="px-3 py-2.5 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                    {t('wizard.usageShort')}
                  </th>
                  <th className="px-3 py-2.5 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('common.status')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {rows.map((row) => (
                  <tr
                    key={row.ingredientId}
                    className={
                      row.discrepancyLevel === 'critical'
                        ? 'bg-red-50/30'
                        : row.discrepancyLevel === 'warning'
                          ? 'bg-yellow-50/30'
                          : ''
                    }
                  >
                    <td className="px-3 py-2.5">
                      <div className="font-medium text-gray-900">
                        {row.ingredientName}
                      </div>
                      <div className="text-xs text-gray-500">{row.unitLabel}</div>
                    </td>
                    <td className="px-3 py-2.5 text-right text-gray-600">
                      {formatQuantity(row.opening, row.unitType, row.unitLabel)}
                    </td>
                    <td className="px-3 py-2.5 text-right text-green-600">
                      {row.deliveries > 0
                        ? `+${formatQuantity(row.deliveries, row.unitType, row.unitLabel)}`
                        : '-'}
                    </td>
                    <td className="px-3 py-2.5 text-right text-blue-600">
                      {row.transfers > 0
                        ? `+${formatQuantity(row.transfers, row.unitType, row.unitLabel)}`
                        : '-'}
                    </td>
                    <td className="px-3 py-2.5 text-right text-red-600">
                      {row.spoilage > 0
                        ? `-${formatQuantity(row.spoilage, row.unitType, row.unitLabel)}`
                        : '-'}
                    </td>
                    <td className="px-3 py-2.5 text-right font-bold text-gray-900 bg-gray-50">
                      {formatQuantity(row.expected, row.unitType, row.unitLabel)}
                    </td>
                    <td className="px-3 py-2.5 bg-primary-50/50">
                      <input
                        type="number"
                        min="0"
                        step={row.unitType === 'weight' ? '0.01' : '1'}
                        value={closingInventory[row.ingredientId] ?? ''}
                        onChange={(e) =>
                          handleInputChange(row.ingredientId, e.target.value)
                        }
                        className="w-20 px-2 py-1 text-right text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="0"
                      />
                    </td>
                    <td className="px-3 py-2.5 text-right font-medium">
                      {row.usage !== null ? (
                        <span
                          className={
                            row.usage > 0
                              ? 'text-orange-600'
                              : row.usage < 0
                                ? 'text-blue-600'
                                : 'text-gray-600'
                          }
                        >
                          {formatQuantity(row.usage, row.unitType, row.unitLabel)}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex justify-center">
                        {getStatusBadge(row)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-xs text-gray-500 pt-4 border-t border-gray-100 mt-4">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-100 border border-green-200"></div>
            <span>OK (&#8804;5%)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-yellow-100 border border-yellow-200"></div>
            <span>{t('wizard.warningLevel')} (5-10%)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-100 border border-red-200"></div>
            <span>{t('wizard.criticalLevel')} (&gt;10%)</span>
          </div>
        </div>
      </div>

      {/* Discrepancy alerts */}
      {alerts.length > 0 && (
        <div className="card">
          <h3 className="card-header">{t('wizard.discrepancies')}</h3>
          <div className="space-y-3">
            {criticalAlerts.length > 0 && (
              <div className="space-y-2">
                {criticalAlerts.map((alert) => (
                  <div
                    key={alert.ingredient_id}
                    className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg"
                  >
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                    <div className="flex-1">
                      <span className="text-sm font-medium text-red-800">
                        {alert.ingredient_name}
                      </span>
                      <span className="text-sm text-red-600 ml-2">
                        {alert.discrepancy_percent.toFixed(1)}%{' '}
                        {t('wizard.discrepancyLabel')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {warningAlerts.length > 0 && (
              <div className="space-y-2">
                {warningAlerts.map((alert) => (
                  <div
                    key={alert.ingredient_id}
                    className="flex items-center gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
                  >
                    <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                    <div className="flex-1">
                      <span className="text-sm font-medium text-yellow-800">
                        {alert.ingredient_name}
                      </span>
                      <span className="text-sm text-yellow-600 ml-2">
                        {alert.discrepancy_percent.toFixed(1)}%{' '}
                        {t('wizard.discrepancyLabel')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Notes */}
      <div className="card">
        <h3 className="card-header">{t('wizard.notes')}</h3>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="input w-full"
          rows={3}
          placeholder={t('wizard.notesPlaceholder')}
        />
      </div>

      {/* Financial summary */}
      <div className="card">
        <h3 className="card-header">{t('wizard.financialSummary')}</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-green-600">{t('wizard.revenue')}</p>
            <p className="text-xl font-bold text-green-800">
              {formatCurrency(daySummary?.total_income_pln ?? 0)}
            </p>
          </div>
          <div className="p-4 bg-red-50 rounded-lg">
            <p className="text-sm text-red-600">{t('wizard.deliveryCosts')}</p>
            <p className="text-xl font-bold text-red-800">
              {formatCurrency(totalDeliveryCost)}
            </p>
          </div>
          <div className="p-4 bg-primary-50 rounded-lg">
            <p className="text-sm text-primary-600">{t('wizard.grossProfit')}</p>
            <p className="text-xl font-bold text-primary-800">
              {formatCurrency((daySummary?.total_income_pln ?? 0) - totalDeliveryCost)}
            </p>
          </div>
        </div>
      </div>

      {/* Close day button */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">
              {t('wizard.confirmationInfo')}
            </p>
            {alerts.length > 0 && (
              <p className="text-sm text-yellow-600 mt-1">
                {t('wizard.discrepancyNote', { count: alerts.length })}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={handleCloseDay}
            disabled={closeMutation.isPending || !isValid}
            className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {closeMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {t('common.saving')}
              </>
            ) : (
              t('dailyOperations.closeDay')
            )}
          </button>
        </div>

        {/* Error message */}
        {closeMutation.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {t('errors.closeDayFailed')}
          </div>
        )}
      </div>
    </div>
  )
}
