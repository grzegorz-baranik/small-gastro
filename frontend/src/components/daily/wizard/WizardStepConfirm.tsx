import { useTranslation } from 'react-i18next'
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  FileText,
  TrendingUp,
  Package,
} from 'lucide-react'
import { formatCurrency, formatQuantity } from '../../../utils/formatters'
import type { DaySummaryResponse } from '../../../types'
import type {
  CalculatedRow,
  DiscrepancyAlert,
} from '../../../hooks/useClosingCalculations'

interface WizardStepConfirmProps {
  daySummary: DaySummaryResponse | undefined
  rows: CalculatedRow[]
  alerts: DiscrepancyAlert[]
  notes: string
  onNotesChange: (notes: string) => void
}

export default function WizardStepConfirm({
  daySummary,
  rows,
  alerts,
  notes,
  onNotesChange,
}: WizardStepConfirmProps) {
  const { t } = useTranslation()

  if (!daySummary) {
    return (
      <div className="flex justify-center py-8">
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    )
  }

  const criticalAlerts = alerts.filter((a) => a.level === 'critical')
  const warningAlerts = alerts.filter((a) => a.level === 'warning')
  const hasAlerts = alerts.length > 0

  const rowsWithDiscrepancy = rows.filter(
    (r) => r.discrepancyLevel === 'warning' || r.discrepancyLevel === 'critical'
  )

  return (
    <div className="space-y-6">
      {/* Alert summary */}
      {hasAlerts && (
        <div
          className={`p-4 rounded-lg border ${
            criticalAlerts.length > 0
              ? 'bg-red-50 border-red-200'
              : 'bg-yellow-50 border-yellow-200'
          }`}
        >
          <div className="flex items-start gap-3">
            {criticalAlerts.length > 0 ? (
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <h4
                className={`font-medium ${
                  criticalAlerts.length > 0 ? 'text-red-800' : 'text-yellow-800'
                }`}
              >
                {t('wizard.discrepancyWarning')}
              </h4>
              <p
                className={`text-sm mt-1 ${
                  criticalAlerts.length > 0 ? 'text-red-600' : 'text-yellow-600'
                }`}
              >
                {criticalAlerts.length > 0 && (
                  <span>
                    {criticalAlerts.length}{' '}
                    {t('wizard.criticalDiscrepancies', {
                      count: criticalAlerts.length,
                    })}
                  </span>
                )}
                {criticalAlerts.length > 0 && warningAlerts.length > 0 && ', '}
                {warningAlerts.length > 0 && (
                  <span>
                    {warningAlerts.length}{' '}
                    {t('wizard.warningDiscrepancies', {
                      count: warningAlerts.length,
                    })}
                  </span>
                )}
              </p>
              <p
                className={`text-xs mt-2 ${
                  criticalAlerts.length > 0 ? 'text-red-500' : 'text-yellow-500'
                }`}
              >
                {t('wizard.reviewBeforeConfirm')}
              </p>
            </div>
          </div>
        </div>
      )}

      {!hasAlerts && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <div>
              <h4 className="font-medium text-green-800">
                {t('wizard.allLooksGood')}
              </h4>
              <p className="text-sm text-green-600 mt-1">
                {t('wizard.noDiscrepancies')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Closing inventory summary */}
      <div>
        <h3 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
          <Package className="w-4 h-4" />
          {t('wizard.closingSummary')}
        </h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('menu.ingredient')}
                </th>
                <th className="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  {t('wizard.openingShort')}
                </th>
                <th className="px-2 py-2 text-right text-xs font-medium text-green-600 uppercase">
                  +{t('wizard.deliveriesShort')}
                </th>
                <th className="px-2 py-2 text-right text-xs font-medium text-blue-600 uppercase">
                  +{t('wizard.transfersShort')}
                </th>
                <th className="px-2 py-2 text-right text-xs font-medium text-red-600 uppercase">
                  -{t('wizard.spoilageShort')}
                </th>
                <th className="px-2 py-2 text-right text-xs font-medium text-gray-700 uppercase">
                  ={t('wizard.expectedShort')}
                </th>
                <th className="px-2 py-2 text-right text-xs font-medium text-gray-900 uppercase">
                  {t('wizard.closingShort')}
                </th>
                <th className="px-2 py-2 text-right text-xs font-medium text-orange-600 uppercase">
                  {t('wizard.usageShort')}
                </th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  {t('common.status')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((row) => (
                <tr
                  key={row.ingredientId}
                  className={
                    row.discrepancyLevel === 'critical'
                      ? 'bg-red-50/50'
                      : row.discrepancyLevel === 'warning'
                        ? 'bg-yellow-50/50'
                        : ''
                  }
                >
                  <td className="px-2 py-2">
                    <span className="font-medium text-gray-900">
                      {row.ingredientName}
                    </span>
                    <span className="text-xs text-gray-500 ml-1">
                      ({row.unitLabel})
                    </span>
                  </td>
                  <td className="px-2 py-2 text-right text-gray-600">
                    {formatQuantity(row.opening, row.unitType, row.unitLabel)}
                  </td>
                  <td className="px-2 py-2 text-right text-green-600">
                    {row.deliveries > 0
                      ? `+${formatQuantity(row.deliveries, row.unitType, row.unitLabel)}`
                      : '-'}
                  </td>
                  <td className="px-2 py-2 text-right text-blue-600">
                    {row.transfers > 0
                      ? `+${formatQuantity(row.transfers, row.unitType, row.unitLabel)}`
                      : '-'}
                  </td>
                  <td className="px-2 py-2 text-right text-red-600">
                    {row.spoilage > 0
                      ? `-${formatQuantity(row.spoilage, row.unitType, row.unitLabel)}`
                      : '-'}
                  </td>
                  <td className="px-2 py-2 text-right text-gray-700 font-medium">
                    {formatQuantity(row.expected, row.unitType, row.unitLabel)}
                  </td>
                  <td className="px-2 py-2 text-right font-bold text-gray-900">
                    {row.closing !== null
                      ? formatQuantity(row.closing, row.unitType, row.unitLabel)
                      : '-'}
                  </td>
                  <td className="px-2 py-2 text-right font-medium">
                    {row.usage !== null ? (
                      <span
                        className={
                          row.usage > 0
                            ? 'text-orange-600'
                            : row.usage < 0
                              ? 'text-blue-600'
                              : 'text-gray-400'
                        }
                      >
                        {row.usage > 0 ? `-${formatQuantity(row.usage, row.unitType, row.unitLabel)}` : formatQuantity(row.usage, row.unitType, row.unitLabel)}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-2 py-2 text-center">
                    {row.discrepancyLevel === 'ok' && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        OK
                      </span>
                    )}
                    {row.discrepancyLevel === 'warning' && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                        {row.discrepancyPercent?.toFixed(0)}%
                      </span>
                    )}
                    {row.discrepancyLevel === 'critical' && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                        {row.discrepancyPercent?.toFixed(0)}%
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Formula legend */}
        <div className="mt-2 text-xs text-gray-500">
          <span className="font-medium">{t('reports.formula')}:</span>{' '}
          {t('wizard.openingShort')} + {t('wizard.deliveriesShort')} + {t('wizard.transfersShort')} - {t('wizard.spoilageShort')} = {t('wizard.expectedShort')}
        </div>
      </div>

      {/* Financial summary */}
      <div>
        <h3 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
          <TrendingUp className="w-4 h-4" />
          {t('wizard.financialSummary')}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="text-xs text-green-600 uppercase font-medium">
              {t('wizard.revenue')}
            </div>
            <div className="text-xl font-bold text-green-800 mt-1">
              {formatCurrency(daySummary.total_income_pln || 0)}
            </div>
          </div>
          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="text-xs text-red-600 uppercase font-medium">
              {t('wizard.deliveryCosts')}
            </div>
            <div className="text-xl font-bold text-red-800 mt-1">
              {formatCurrency(daySummary.events.deliveries_total_pln || 0)}
            </div>
          </div>
          <div className="p-4 bg-primary-50 rounded-lg border border-primary-200">
            <div className="text-xs text-primary-600 uppercase font-medium">
              {t('wizard.grossProfit')}
            </div>
            <div className="text-xl font-bold text-primary-800 mt-1">
              {formatCurrency(
                (daySummary.total_income_pln || 0) -
                  (daySummary.events.deliveries_total_pln || 0)
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Notes field */}
      <div>
        <h3 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
          <FileText className="w-4 h-4" />
          {t('wizard.notes')} <span className="text-gray-400 font-normal">({t('common.optional')})</span>
        </h3>
        <textarea
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          placeholder={t('wizard.notesPlaceholder')}
        />
      </div>

      {/* Final confirmation message */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-600">
          {t('wizard.confirmationInfo')}
        </p>
        {rowsWithDiscrepancy.length > 0 && (
          <p className="text-xs text-amber-600 mt-2">
            {t('wizard.discrepancyNote', { count: rowsWithDiscrepancy.length })}
          </p>
        )}
      </div>
    </div>
  )
}
