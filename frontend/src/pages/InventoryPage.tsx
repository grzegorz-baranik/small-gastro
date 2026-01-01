import { useQuery } from '@tanstack/react-query'
import { getDailyRecords, getDaySummary } from '../api/dailyRecords'
import { formatDate, formatQuantity } from '../utils/formatters'
import { AlertTriangle, CheckCircle } from 'lucide-react'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { CalculatedSalesTable } from '../components/daily'
import { useState } from 'react'

export default function InventoryPage() {
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null)

  const { data: recordsData, isLoading: recordsLoading } = useQuery({
    queryKey: ['dailyRecords'],
    queryFn: () => getDailyRecords(),
  })

  const records = recordsData?.items || []

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dailySummary', selectedRecordId],
    queryFn: () => getDaySummary(selectedRecordId!),
    enabled: !!selectedRecordId,
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Historia magazynowa</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Records List */}
        <div className="card lg:col-span-1">
          <h2 className="card-header">Dni</h2>
          {recordsLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="space-y-2">
              {records.map((record) => (
                <button
                  key={record.id}
                  onClick={() => setSelectedRecordId(record.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedRecordId === record.id
                      ? 'bg-primary-50 border border-primary-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900">{formatDate(record.date)}</p>
                    <span className={`text-xs px-2 py-1 rounded ${
                      record.status === 'closed'
                        ? 'bg-gray-100 text-gray-600'
                        : 'bg-green-100 text-green-700'
                    }`}>
                      {record.status === 'closed' ? 'Zamkniety' : 'Otwarty'}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Details */}
        <div className="card lg:col-span-2">
          {selectedRecordId ? (
            summaryLoading ? (
              <LoadingSpinner />
            ) : summary ? (
              <div className="space-y-6">
                <div>
                  <h2 className="card-header">Podsumowanie dnia {formatDate(summary.daily_record?.date || '')}</h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Sprzedane produkty</p>
                      <p className="text-xl font-bold text-gray-900">{summary.calculated_sales?.length || 0}</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <p className="text-sm text-gray-500">Przychody</p>
                      <p className="text-xl font-bold text-green-600">{summary.total_income_pln || 0} zl</p>
                    </div>
                    <div className="p-4 bg-red-50 rounded-lg">
                      <p className="text-sm text-gray-500">Dostawy</p>
                      <p className="text-xl font-bold text-red-600">{summary.events?.deliveries_total_pln || 0} zl</p>
                    </div>
                  </div>
                </div>

                {/* Calculated Sales */}
                {summary.calculated_sales && summary.calculated_sales.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Obliczona sprzedaz</h3>
                    <CalculatedSalesTable
                      sales={summary.calculated_sales}
                      totalIncome={summary.total_income_pln || 0}
                    />
                  </div>
                )}

                {/* Usage Items with Discrepancies */}
                {summary.usage_items && summary.usage_items.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Zuzycie skladnikow</h3>
                    <div className="space-y-2">
                      {summary.usage_items.map((item) => {
                        const hasIssue = item.discrepancy_level && item.discrepancy_level !== 'ok'
                        return (
                          <div
                            key={item.ingredient_id}
                            className={`p-3 rounded-lg ${
                              hasIssue ? 'bg-yellow-50 border border-yellow-200' : 'bg-gray-50'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                {hasIssue ? (
                                  <AlertTriangle className="w-4 h-4 text-yellow-600" />
                                ) : (
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                )}
                                <span className="font-medium text-gray-900">{item.ingredient_name}</span>
                              </div>
                              {item.discrepancy_percent !== null && (
                                <span className={`text-sm font-medium ${
                                  Math.abs(item.discrepancy_percent) > 10 ? 'text-red-600' : 'text-gray-600'
                                }`}>
                                  {item.discrepancy_percent > 0 ? '+' : ''}{item.discrepancy_percent.toFixed(1)}%
                                </span>
                              )}
                            </div>
                            <div className="mt-2 grid grid-cols-4 gap-2 text-sm text-gray-600">
                              <div>
                                <p className="text-xs text-gray-400">Poczatek</p>
                                <p>{formatQuantity(item.opening_quantity, item.unit_type)}</p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-400">Koniec</p>
                                <p>{formatQuantity(item.closing_quantity || 0, item.unit_type)}</p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-400">Zuzycie</p>
                                <p>{formatQuantity(item.usage || 0, item.unit_type)}</p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-400">Roznica</p>
                                <p className={Math.abs(item.discrepancy || 0) > 0.01 ? 'text-red-600 font-medium' : ''}>
                                  {formatQuantity(item.discrepancy || 0, item.unit_type)}
                                </p>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : null
          ) : (
            <div className="text-center py-12 text-gray-500">
              Wybierz dzien z listy, aby zobaczyc szczegoly
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
