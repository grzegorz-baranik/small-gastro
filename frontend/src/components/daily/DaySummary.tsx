import { useQuery } from '@tanstack/react-query'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  Clock,
  Package,
  Truck,
  Trash2,
} from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import CalculatedSalesTable from './CalculatedSalesTable'
import { getDaySummary } from '../../api/dailyOperations'
import { formatCurrency, formatDate, formatDateTime, formatQuantity } from '../../utils/formatters'
import type { DailyRecord, UsageItem, DiscrepancyAlert } from '../../types'

interface DaySummaryProps {
  isOpen: boolean
  onClose: () => void
  dailyRecord: DailyRecord
}

export default function DaySummary({ isOpen, onClose, dailyRecord }: DaySummaryProps) {
  // Fetch day summary
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['daySummary', dailyRecord.id],
    queryFn: () => getDaySummary(dailyRecord.id),
    enabled: isOpen,
  })

  // Get discrepancy icon
  const getDiscrepancyIcon = (level: 'ok' | 'warning' | 'critical' | null) => {
    switch (level) {
      case 'ok':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return null
    }
  }

  // Get discrepancy color class
  const getDiscrepancyColorClass = (level: 'ok' | 'warning' | 'critical' | null) => {
    switch (level) {
      case 'ok':
        return 'text-green-600 bg-green-50'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50'
      case 'critical':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-500'
    }
  }

  // Get status badge
  const getStatusBadge = (status: string) => {
    if (status === 'open') {
      return (
        <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
          OTWARTY
        </span>
      )
    }
    return (
      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
        ZAMKNIETY
      </span>
    )
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Podsumowanie dnia: ${formatDate(dailyRecord.date)}`} size="2xl">
      {isLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-red-800">Nie udalo sie zaladowac podsumowania</p>
        </div>
      ) : summary ? (
        <div className="space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Header with status */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-900">
                {formatDate(dailyRecord.date)}
              </h3>
              <p className="text-sm text-gray-500">
                {getDayName(dailyRecord.date)}
              </p>
            </div>
            {getStatusBadge(summary.daily_record.status)}
          </div>

          {/* Time info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Clock className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Otwarcie</p>
                <p className="font-medium text-gray-900">
                  {summary.opening_time
                    ? formatDateTime(summary.opening_time)
                    : '-'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Clock className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Zamkniecie</p>
                <p className="font-medium text-gray-900">
                  {summary.closing_time
                    ? formatDateTime(summary.closing_time)
                    : '-'}
                </p>
              </div>
            </div>
          </div>

          {/* Events summary */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              Wydarzenia dnia
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                <Truck className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-xs text-green-600">Dostawy</p>
                  <p className="font-medium text-green-800">
                    {summary.events.deliveries_count} pozycji
                  </p>
                  <p className="text-xs text-green-600">
                    {formatCurrency(summary.events.deliveries_total_pln)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                <Package className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="text-xs text-blue-600">Transfery</p>
                  <p className="font-medium text-blue-800">
                    {summary.events.transfers_count} pozycji
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg">
                <Trash2 className="w-5 h-5 text-red-600" />
                <div>
                  <p className="text-xs text-red-600">Straty</p>
                  <p className="font-medium text-red-800">
                    {summary.events.spoilage_count} pozycji
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Inventory usage */}
          {summary.usage_items.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Zuzycie skladnikow
              </h4>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Skladnik
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                        Otwarcie
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                        Zamkniecie
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                        Zuzycie
                      </th>
                      <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {summary.usage_items.map((item: UsageItem) => (
                      <tr key={item.ingredient_id}>
                        <td className="px-4 py-2">
                          <div className="font-medium text-gray-900">
                            {item.ingredient_name}
                          </div>
                          <div className="text-xs text-gray-500">
                            {item.unit_label}
                          </div>
                        </td>
                        <td className="px-4 py-2 text-right text-gray-600">
                          {formatQuantity(item.opening_quantity, item.unit_type)}
                        </td>
                        <td className="px-4 py-2 text-right text-gray-600">
                          {item.closing_quantity !== null
                            ? formatQuantity(item.closing_quantity, item.unit_type)
                            : '-'}
                        </td>
                        <td className="px-4 py-2 text-right font-medium text-gray-900">
                          {item.usage !== null
                            ? formatQuantity(item.usage, item.unit_type)
                            : '-'}
                        </td>
                        <td className="px-4 py-2">
                          {item.discrepancy_level && (
                            <div
                              className={`flex items-center justify-center gap-1 px-2 py-1 rounded ${getDiscrepancyColorClass(item.discrepancy_level)}`}
                            >
                              {getDiscrepancyIcon(item.discrepancy_level)}
                              <span className="text-xs font-medium">
                                {item.discrepancy_percent !== null
                                  ? `${item.discrepancy_percent.toFixed(1)}%`
                                  : '-'}
                              </span>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Discrepancy alerts */}
          {summary.discrepancy_alerts.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Alerty rozbieznosci
              </h4>
              <div className="space-y-2">
                {summary.discrepancy_alerts.map((alert: DiscrepancyAlert) => (
                  <div
                    key={alert.ingredient_id}
                    className={`flex items-center gap-2 p-3 rounded-lg ${getDiscrepancyColorClass(alert.level)}`}
                  >
                    {getDiscrepancyIcon(alert.level)}
                    <span className="text-sm font-medium">{alert.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Calculated sales */}
          {summary.calculated_sales.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Obliczona sprzedaz
              </h4>
              <CalculatedSalesTable
                sales={summary.calculated_sales}
                totalIncome={summary.total_income_pln}
              />
            </div>
          )}

          {/* Financial summary */}
          <div className="p-4 bg-primary-50 rounded-lg">
            <h4 className="text-sm font-medium text-primary-800 mb-3">
              Podsumowanie finansowe
            </h4>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-primary-600">Przychod</p>
                <p className="text-lg font-bold text-primary-900">
                  {formatCurrency(summary.total_income_pln)}
                </p>
              </div>
              <div>
                <p className="text-xs text-primary-600">Koszty dostaw</p>
                <p className="text-lg font-bold text-primary-900">
                  {formatCurrency(summary.events.deliveries_total_pln)}
                </p>
              </div>
              <div>
                <p className="text-xs text-primary-600">Zysk brutto</p>
                <p className="text-lg font-bold text-primary-900">
                  {formatCurrency(
                    summary.total_income_pln - summary.events.deliveries_total_pln
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Notes */}
          {summary.daily_record.notes && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Notatki</h4>
              <p className="text-gray-600">{summary.daily_record.notes}</p>
            </div>
          )}

          {/* Close button */}
          <div className="pt-4 sticky bottom-0 bg-white">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary w-full"
            >
              Zamknij
            </button>
          </div>
        </div>
      ) : null}
    </Modal>
  )
}

// Helper function to get Polish day name
function getDayName(dateString: string): string {
  const date = new Date(dateString)
  const dayNames = [
    'Niedziela',
    'Poniedzialek',
    'Wtorek',
    'Sroda',
    'Czwartek',
    'Piatek',
    'Sobota',
  ]
  return dayNames[date.getDay()]
}
