import { useTranslation } from 'react-i18next'
import { CheckCircle, AlertTriangle, AlertCircle, Copy } from 'lucide-react'
import { formatQuantity } from '../../../utils/formatters'
import type { CalculatedRow, DiscrepancyAlert } from '../../../hooks/useClosingCalculations'

interface WizardStepClosingProps {
  rows: CalculatedRow[]
  closingInventory: Record<number, string>
  onChange: (inventory: Record<number, string>) => void
  alerts: DiscrepancyAlert[]
}

export default function WizardStepClosing({
  rows,
  closingInventory,
  onChange,
  alerts,
}: WizardStepClosingProps) {
  const { t } = useTranslation()

  const handleInputChange = (ingredientId: number, value: string) => {
    onChange({
      ...closingInventory,
      [ingredientId]: value,
    })
  }

  const handleCopyExpected = () => {
    const newInventory: Record<number, string> = {}
    rows.forEach((row) => {
      newInventory[row.ingredientId] = row.expected.toString()
    })
    onChange(newInventory)
  }

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

  const warningAlerts = alerts.filter((a) => a.level === 'warning')
  const criticalAlerts = alerts.filter((a) => a.level === 'critical')

  return (
    <div className="space-y-5">
      {/* Formula explanation and action button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 bg-gray-50 rounded-lg">
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
          data-testid="copy-expected-btn"
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
        >
          <Copy className="w-4 h-4" />
          {t('wizard.copyExpected')}
        </button>
      </div>

      {/* Table with live calculations */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="closing-inventory-table">
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
                      data-testid={`closing-qty-input-${row.ingredientId}`}
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
                  <td className="px-3 py-2.5" data-testid={`closing-status-${row.ingredientId}`}>
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

      {/* Discrepancy alerts */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">
            {t('wizard.discrepancies')}
          </h4>

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
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-gray-500 pt-2 border-t border-gray-100">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-green-100 border border-green-200"></div>
          <span>OK (≤5%)</span>
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
  )
}
