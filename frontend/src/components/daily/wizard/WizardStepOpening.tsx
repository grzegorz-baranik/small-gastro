import { useTranslation } from 'react-i18next'
import { Calendar, Info } from 'lucide-react'
import { formatDateTime, formatQuantity } from '../../../utils/formatters'
import type { DaySummaryResponse, PreviousClosingItem } from '../../../types'

interface WizardStepOpeningProps {
  daySummary: DaySummaryResponse | undefined
  previousClosing: PreviousClosingItem[] | undefined
}

export default function WizardStepOpening({
  daySummary,
  previousClosing,
}: WizardStepOpeningProps) {
  const { t } = useTranslation()

  if (!daySummary) {
    return (
      <div className="flex justify-center py-8">
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    )
  }

  const openingTime = daySummary.opening_time
    ? formatDateTime(daySummary.opening_time)
    : '-'

  return (
    <div className="space-y-6">
      {/* Opening date/time header */}
      <div className="flex items-center gap-3 p-4 bg-primary-50 rounded-lg">
        <Calendar className="w-5 h-5 text-primary-600" />
        <div>
          <span className="text-sm text-gray-600">{t('wizard.openedAt')}:</span>
          <span className="ml-2 font-medium text-gray-900">{openingTime}</span>
        </div>
      </div>

      {/* Previous day comparison (if available) */}
      {previousClosing && previousClosing.length > 0 && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-800">
                {t('wizard.previousDayComparison')}
              </p>
              <p className="text-xs text-blue-600 mt-1">
                {t('wizard.previousDayInfo')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Opening inventory table */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          {t('wizard.openingInventory')}
        </h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm" data-testid="opening-inventory-table">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('menu.ingredient')}
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('wizard.openingQty')}
                </th>
                {previousClosing && previousClosing.length > 0 && (
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('wizard.previousClosing')}
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {daySummary.usage_items.map((item) => {
                const prevItem = previousClosing?.find(
                  (p) => p.ingredient_id === item.ingredient_id
                )
                const hasDiff = prevItem && prevItem.quantity !== item.opening_quantity

                return (
                  <tr key={item.ingredient_id} data-testid={`opening-row-${item.ingredient_id}`}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">
                        {item.ingredient_name}
                      </div>
                      <div className="text-xs text-gray-500">{item.unit_label}</div>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      {formatQuantity(item.opening_quantity, item.unit_type, item.unit_label)}
                    </td>
                    {previousClosing && previousClosing.length > 0 && (
                      <td className={`px-4 py-3 text-right ${hasDiff ? 'text-amber-600' : 'text-gray-500'}`}>
                        {prevItem
                          ? formatQuantity(prevItem.quantity, item.unit_type, item.unit_label)
                          : '-'}
                        {hasDiff && (
                          <span className="ml-1 text-xs">
                            ({item.opening_quantity > prevItem!.quantity ? '+' : ''}
                            {(item.opening_quantity - prevItem!.quantity).toFixed(item.unit_type === 'weight' ? 2 : 0)})
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info message */}
      <div className="flex items-start gap-2 p-4 bg-gray-50 rounded-lg">
        <Info className="w-5 h-5 text-gray-400 mt-0.5" />
        <div className="text-sm text-gray-600">
          <p>{t('wizard.infoOpeningValues')}</p>
          <p className="mt-1">{t('wizard.continueToEvents')}</p>
        </div>
      </div>
    </div>
  )
}
