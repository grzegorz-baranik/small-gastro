import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Package, Trash2, FileSpreadsheet, Calendar } from 'lucide-react'
import {
  getMonthlyTrendsReport,
  exportMonthlyTrendsExcel,
  getIngredientUsageReport,
  exportIngredientUsageExcel,
  getSpoilageReport,
  exportSpoilageExcel,
} from '../api/reports'
import { getIngredients } from '../api/ingredients'
import { formatCurrency, formatDate } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import type { DateRangeRequest, SpoilageReason } from '../types'

type ReportTab = 'trends' | 'usage' | 'spoilage'

const SPOILAGE_REASON_LABELS: Record<SpoilageReason, string> = {
  expired: 'Przeterminowane',
  damaged: 'Uszkodzone',
  quality: 'Niska jakosc',
  other: 'Inne',
}

function getDefaultDateRange(): DateRangeRequest {
  const today = new Date()
  const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
  return {
    start_date: firstDayOfMonth.toISOString().split('T')[0],
    end_date: today.toISOString().split('T')[0],
  }
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<ReportTab>('trends')
  const [dateRange, setDateRange] = useState<DateRangeRequest>(getDefaultDateRange)
  const [selectedIngredients, setSelectedIngredients] = useState<number[]>([])
  const [isExporting, setIsExporting] = useState(false)

  const tabs = [
    { id: 'trends' as ReportTab, label: 'Trendy miesieczne', icon: TrendingUp },
    { id: 'usage' as ReportTab, label: 'Zuzycie skladnikow', icon: Package },
    { id: 'spoilage' as ReportTab, label: 'Straty', icon: Trash2 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Raporty</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Date Range Selector */}
      <div className="card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Zakres dat:</span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={dateRange.start_date}
              onChange={(e) => setDateRange((prev) => ({ ...prev, start_date: e.target.value }))}
              className="input w-auto"
            />
            <span className="text-gray-500">do</span>
            <input
              type="date"
              value={dateRange.end_date}
              onChange={(e) => setDateRange((prev) => ({ ...prev, end_date: e.target.value }))}
              className="input w-auto"
            />
          </div>
        </div>
      </div>

      {/* Report Content */}
      {activeTab === 'trends' && (
        <MonthlyTrendsReport
          dateRange={dateRange}
          isExporting={isExporting}
          setIsExporting={setIsExporting}
        />
      )}
      {activeTab === 'usage' && (
        <IngredientUsageReport
          dateRange={dateRange}
          selectedIngredients={selectedIngredients}
          setSelectedIngredients={setSelectedIngredients}
          isExporting={isExporting}
          setIsExporting={setIsExporting}
        />
      )}
      {activeTab === 'spoilage' && (
        <SpoilageReportSection
          dateRange={dateRange}
          isExporting={isExporting}
          setIsExporting={setIsExporting}
        />
      )}
    </div>
  )
}

interface ReportSectionProps {
  dateRange: DateRangeRequest
  isExporting: boolean
  setIsExporting: (value: boolean) => void
}

function MonthlyTrendsReport({ dateRange, isExporting, setIsExporting }: ReportSectionProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['monthly-trends', dateRange],
    queryFn: () => getMonthlyTrendsReport(dateRange),
    enabled: !!dateRange.start_date && !!dateRange.end_date,
  })

  const handleExport = async () => {
    setIsExporting(true)
    try {
      await exportMonthlyTrendsExcel(dateRange)
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <div className="card text-red-600">Blad ladowania raportu</div>

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-sm text-gray-500">Laczny przychod</p>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(data.total_income_pln)}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Laczne koszty</p>
            <p className="text-2xl font-bold text-red-600">{formatCurrency(data.total_costs_pln)}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Sredni dzienny przychod</p>
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(data.avg_daily_income_pln)}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Najlepszy dzien</p>
            {data.best_day ? (
              <p className="text-lg font-bold text-green-600">
                {formatDate(data.best_day.date)}: {formatCurrency(data.best_day.income_pln)}
              </p>
            ) : (
              <p className="text-gray-400">Brak danych</p>
            )}
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Szczegoly dzienne</h3>
          <button
            onClick={handleExport}
            disabled={isExporting || !data?.items.length}
            className="btn btn-secondary flex items-center gap-2"
          >
            {isExporting ? (
              <LoadingSpinner size="sm" />
            ) : (
              <FileSpreadsheet className="w-4 h-4" />
            )}
            Eksportuj do Excel
          </button>
        </div>

        {!data?.items.length ? (
          <p className="text-gray-500 text-center py-8">Brak danych dla wybranego zakresu</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Data</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Przychod</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Dostawy</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Straty</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Zysk</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.date} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">{formatDate(item.date)}</td>
                    <td className="py-3 px-4 text-right text-green-600 font-medium">
                      {formatCurrency(item.income_pln)}
                    </td>
                    <td className="py-3 px-4 text-right text-red-600">
                      {formatCurrency(item.delivery_cost_pln)}
                    </td>
                    <td className="py-3 px-4 text-right text-red-600">
                      {formatCurrency(item.spoilage_cost_pln)}
                    </td>
                    <td className={`py-3 px-4 text-right font-bold ${item.profit_pln >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(item.profit_pln)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

interface IngredientUsageReportProps extends ReportSectionProps {
  selectedIngredients: number[]
  setSelectedIngredients: (value: number[]) => void
}

function IngredientUsageReport({
  dateRange,
  selectedIngredients,
  setSelectedIngredients,
  isExporting,
  setIsExporting,
}: IngredientUsageReportProps) {
  const { data: ingredientsData } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['ingredient-usage', dateRange, selectedIngredients],
    queryFn: () => getIngredientUsageReport(dateRange, selectedIngredients.length > 0 ? selectedIngredients : undefined),
    enabled: !!dateRange.start_date && !!dateRange.end_date,
  })

  const handleExport = async () => {
    setIsExporting(true)
    try {
      await exportIngredientUsageExcel(dateRange, selectedIngredients.length > 0 ? selectedIngredients : undefined)
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const toggleIngredient = (id: number) => {
    setSelectedIngredients(
      selectedIngredients.includes(id)
        ? selectedIngredients.filter((i) => i !== id)
        : [...selectedIngredients, id]
    )
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <div className="card text-red-600">Blad ladowania raportu</div>

  return (
    <div className="space-y-6">
      {/* Ingredient Filter */}
      {ingredientsData && ingredientsData.items.length > 0 && (
        <div className="card">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Filtruj skladniki (opcjonalnie):</h4>
          <div className="flex flex-wrap gap-2">
            {ingredientsData.items.map((ingredient) => (
              <button
                key={ingredient.id}
                onClick={() => toggleIngredient(ingredient.id)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedIngredients.includes(ingredient.id)
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {ingredient.name}
              </button>
            ))}
            {selectedIngredients.length > 0 && (
              <button
                onClick={() => setSelectedIngredients([])}
                className="px-3 py-1 rounded-full text-sm font-medium bg-gray-300 text-gray-700 hover:bg-gray-400"
              >
                Wyczysc filtry
              </button>
            )}
          </div>
        </div>
      )}

      {/* Summary */}
      {data && data.summary.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Podsumowanie zuzycia</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.summary.map((item) => (
              <div key={item.ingredient_id} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">{item.ingredient_name}</p>
                <p className="text-xl font-bold text-gray-900">
                  {item.total_used.toFixed(item.unit_label === 'szt.' ? 0 : 2)} {item.unit_label}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Szczegoly zuzycia</h3>
          <button
            onClick={handleExport}
            disabled={isExporting || !data?.items.length}
            className="btn btn-secondary flex items-center gap-2"
          >
            {isExporting ? (
              <LoadingSpinner size="sm" />
            ) : (
              <FileSpreadsheet className="w-4 h-4" />
            )}
            Eksportuj do Excel
          </button>
        </div>

        {!data?.items.length ? (
          <p className="text-gray-500 text-center py-8">Brak danych dla wybranego zakresu</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Data</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Skladnik</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Otwarcie</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Zuzycie</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Zamkniecie</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item, index) => (
                  <tr key={`${item.date}-${item.ingredient_id}-${index}`} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">{formatDate(item.date)}</td>
                    <td className="py-3 px-4">{item.ingredient_name}</td>
                    <td className="py-3 px-4 text-right">
                      {item.opening_quantity.toFixed(item.unit_label === 'szt.' ? 0 : 2)} {item.unit_label}
                    </td>
                    <td className="py-3 px-4 text-right font-medium text-orange-600">
                      {item.used_quantity.toFixed(item.unit_label === 'szt.' ? 0 : 2)} {item.unit_label}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {item.closing_quantity.toFixed(item.unit_label === 'szt.' ? 0 : 2)} {item.unit_label}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function SpoilageReportSection({ dateRange, isExporting, setIsExporting }: ReportSectionProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['spoilage-report', dateRange],
    queryFn: () => getSpoilageReport(dateRange),
    enabled: !!dateRange.start_date && !!dateRange.end_date,
  })

  const handleExport = async () => {
    setIsExporting(true)
    try {
      await exportSpoilageExcel(dateRange)
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <div className="card text-red-600">Blad ladowania raportu</div>

  return (
    <div className="space-y-6">
      {/* Summary by Reason */}
      {data && data.summary_by_reason.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Podsumowanie wg przyczyny</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.summary_by_reason.map((item) => (
              <div key={item.reason} className="p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-gray-500">{SPOILAGE_REASON_LABELS[item.reason]}</p>
                <p className="text-xl font-bold text-red-600">{item.count} pozycji</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary by Ingredient */}
      {data && data.summary_by_ingredient.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Podsumowanie wg skladnika</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.summary_by_ingredient.map((item) => (
              <div key={item.ingredient_id} className="p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-gray-500">{item.ingredient_name}</p>
                <p className="text-xl font-bold text-orange-600">
                  {item.total_quantity.toFixed(item.unit_label === 'szt.' ? 0 : 2)} {item.unit_label}
                </p>
                <p className="text-sm text-gray-400">{item.count} przypadkow</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Lista strat</h3>
          <button
            onClick={handleExport}
            disabled={isExporting || !data?.items.length}
            className="btn btn-secondary flex items-center gap-2"
          >
            {isExporting ? (
              <LoadingSpinner size="sm" />
            ) : (
              <FileSpreadsheet className="w-4 h-4" />
            )}
            Eksportuj do Excel
          </button>
        </div>

        {!data?.items.length ? (
          <p className="text-gray-500 text-center py-8">Brak strat dla wybranego zakresu</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Data</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Skladnik</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Ilosc</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Przyczyna</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Notatki</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item, index) => (
                  <tr key={`${item.date}-${item.ingredient_id}-${index}`} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">{formatDate(item.date)}</td>
                    <td className="py-3 px-4">{item.ingredient_name}</td>
                    <td className="py-3 px-4 text-right font-medium text-red-600">
                      {item.quantity.toFixed(item.unit_label === 'szt.' ? 0 : 2)} {item.unit_label}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                        {SPOILAGE_REASON_LABELS[item.reason]}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-500">{item.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
