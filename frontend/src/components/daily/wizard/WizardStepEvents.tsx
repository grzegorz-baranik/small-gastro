import { useTranslation } from 'react-i18next'
import { Truck, Package, Trash2, Info } from 'lucide-react'
import { formatCurrency, formatQuantity } from '../../../utils/formatters'
import type { DaySummaryResponse, DeliverySummaryItem, TransferSummaryItem, SpoilageSummaryItem } from '../../../types'

interface WizardStepEventsProps {
  daySummary: DaySummaryResponse | undefined
  deliveries: DeliverySummaryItem[]
  transfers: TransferSummaryItem[]
  spoilage: SpoilageSummaryItem[]
}

const SPOILAGE_REASON_LABELS: Record<string, string> = {
  expired: 'Przeterminowane',
  over_prepared: 'Nadmiar przygotowany',
  contaminated: 'Zanieczyszczone',
  equipment_failure: 'Awaria sprzętu',
  other: 'Inne',
}

export default function WizardStepEvents({
  daySummary,
  deliveries,
  transfers,
  spoilage,
}: WizardStepEventsProps) {
  const { t } = useTranslation()

  if (!daySummary) {
    return (
      <div className="flex justify-center py-8">
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    )
  }

  const hasNoEvents =
    daySummary.events.deliveries_count === 0 &&
    daySummary.events.transfers_count === 0 &&
    daySummary.events.spoilage_count === 0

  if (hasNoEvents) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Info className="w-12 h-12 text-gray-400 mb-4" />
        <p className="text-gray-600 text-lg">{t('wizard.noEventsToday')}</p>
        <p className="text-gray-500 text-sm mt-2">
          {t('wizard.noEventsInfo')}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Deliveries section */}
      {daySummary.events.deliveries_count > 0 && (
        <div className="border border-green-200 rounded-lg overflow-hidden">
          <div className="bg-green-50 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Truck className="w-5 h-5 text-green-600" />
              <span className="font-medium text-green-800">
                {t('wizard.deliveries')} ({daySummary.events.deliveries_count})
              </span>
            </div>
            <span className="font-medium text-green-700">
              {formatCurrency(daySummary.events.deliveries_total_pln)}
            </span>
          </div>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {deliveries.map((delivery) => (
                <tr key={delivery.id}>
                  <td className="px-4 py-2 text-gray-900">
                    {delivery.ingredient_name}
                  </td>
                  <td className="px-4 py-2 text-right text-green-600 font-medium">
                    +{delivery.quantity} {delivery.unit_label}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-600">
                    {formatCurrency(delivery.price_pln)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Transfers section */}
      {daySummary.events.transfers_count > 0 && (
        <div className="border border-blue-200 rounded-lg overflow-hidden">
          <div className="bg-blue-50 px-4 py-3 flex items-center gap-2">
            <Package className="w-5 h-5 text-blue-600" />
            <span className="font-medium text-blue-800">
              {t('wizard.transfers')} ({daySummary.events.transfers_count})
            </span>
          </div>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {transfers.map((transfer) => (
                <tr key={transfer.id}>
                  <td className="px-4 py-2 text-gray-900">
                    {transfer.ingredient_name}
                  </td>
                  <td className="px-4 py-2 text-right text-blue-600 font-medium">
                    +{transfer.quantity} {transfer.unit_label}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-500 text-xs">
                    {t('wizard.fromStorage')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Spoilage section */}
      {daySummary.events.spoilage_count > 0 && (
        <div className="border border-red-200 rounded-lg overflow-hidden">
          <div className="bg-red-50 px-4 py-3 flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-red-600" />
            <span className="font-medium text-red-800">
              {t('wizard.spoilage')} ({daySummary.events.spoilage_count})
            </span>
          </div>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {spoilage.map((item) => (
                <tr key={item.id}>
                  <td className="px-4 py-2 text-gray-900">
                    {item.ingredient_name}
                  </td>
                  <td className="px-4 py-2 text-right text-red-600 font-medium">
                    -{item.quantity} {item.unit_label}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-500 text-xs">
                    {SPOILAGE_REASON_LABELS[item.reason] || item.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Impact summary table */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          {t('wizard.impactSummary')}
        </h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('menu.ingredient')}
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  {t('wizard.openingQty')}
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-green-600 uppercase">
                  +{t('wizard.deliveriesShort')}
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-blue-600 uppercase">
                  +{t('wizard.transfersShort')}
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-red-600 uppercase">
                  -{t('wizard.spoilageShort')}
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">
                  ={t('wizard.expectedShort')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {daySummary.usage_items.map((item) => (
                <tr key={item.ingredient_id}>
                  <td className="px-3 py-2 text-gray-900 font-medium">
                    {item.ingredient_name}
                  </td>
                  <td className="px-3 py-2 text-right text-gray-600">
                    {formatQuantity(item.opening_quantity, item.unit_type, item.unit_label)}
                  </td>
                  <td className="px-3 py-2 text-right text-green-600">
                    {item.deliveries_quantity > 0
                      ? `+${formatQuantity(item.deliveries_quantity, item.unit_type, item.unit_label)}`
                      : '-'}
                  </td>
                  <td className="px-3 py-2 text-right text-blue-600">
                    {item.transfers_quantity > 0
                      ? `+${formatQuantity(item.transfers_quantity, item.unit_type, item.unit_label)}`
                      : '-'}
                  </td>
                  <td className="px-3 py-2 text-right text-red-600">
                    {item.spoilage_quantity > 0
                      ? `-${formatQuantity(item.spoilage_quantity, item.unit_type, item.unit_label)}`
                      : '-'}
                  </td>
                  <td className="px-3 py-2 text-right text-gray-900 font-bold">
                    {formatQuantity(item.expected_closing, item.unit_type, item.unit_label)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
