import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Package, Trash2, FileSpreadsheet, Calendar, Users } from 'lucide-react'
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
import { WageAnalyticsSection } from '../components/employees'
import type { DateRangeRequest, SpoilageReason } from '../types'

type ReportTab = 'trends' | 'usage' | 'spoilage' | 'wages'

function getDefaultDateRange(): DateRangeRequest {
  const today = new Date()
  const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
  return {
    start_date: firstDayOfMonth.toISOString().split('T')[0],
    end_date: today.toISOString().split('T')[0],
  }
}

export default function ReportsPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<ReportTab>('trends')
  const [dateRange, setDateRange] = useState<DateRangeRequest>(getDefaultDateRange)
  const [selectedIngredients, setSelectedIngredients] = useState<number[]>([])
  const [isExporting, setIsExporting] = useState(false)

  const tabs = [
    { id: 'trends' as ReportTab, label: t('reports.monthlyTrends'), icon: TrendingUp },
    { id: 'usage' as ReportTab, label: t('reports.ingredientUsage'), icon: Package },
    { id: 'spoilage' as ReportTab, label: t('reports.spoilage'), icon: Trash2 },
    { id: 'wages' as ReportTab, label: t('employees.wages'), icon: Users },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('reports.title')}</h1>
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

      {/* Date Range Selector - hide for wages tab which has its own date selector */}
      {activeTab !== 'wages' && (
        <div className="card">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">{t('reports.dateRange')}</span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={dateRange.start_date}
                onChange={(e) => setDateRange((prev) => ({ ...prev, start_date: e.target.value }))}
                className="input w-auto"
              />
              <span className="text-gray-500">{t('reports.to')}</span>
              <input
                type="date"
                value={dateRange.end_date}
                onChange={(e) => setDateRange((prev) => ({ ...prev, end_date: e.target.value }))}
                className="input w-auto"
              />
            </div>
          </div>
        </div>
      )}

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
      {activeTab === 'wages' && <WageAnalyticsSection />}
    </div>
  )
}

interface ReportSectionProps {
  dateRange: DateRangeRequest
  isExporting: boolean
  setIsExporting: (value: boolean) => void
}

function MonthlyTrendsReport({ dateRange, isExporting, setIsExporting }: ReportSectionProps) {
  const { t } = useTranslation()
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
  if (error) return <div className="card text-red-600">{t('errors.generic')}</div>

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-sm text-gray-500">{t('reports.totalRevenue')}</p>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(data.total_income_pln)}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">{t('reports.totalCosts')}</p>
            <p className="text-2xl font-bold text-red-600">{formatCurrency(data.total_costs_pln)}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">{t('reports.avgDailyRevenue')}</p>
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(data.avg_daily_income_pln)}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">{t('reports.bestDay')}</p>
            {data.best_day ? (
              <p className="text-lg font-bold text-green-600">
                {formatDate(data.best_day.date)}: {formatCurrency(data.best_day.income_pln)}
              </p>
            ) : (
              <p className="text-gray-400">{t('common.noData')}</p>
            )}
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{t('reports.dailyDetails')}</h3>
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
            {t('common.exportToExcel')}
          </button>
        </div>

        {!data?.items.length ? (
          <p className="text-gray-500 text-center py-8">{t('reports.noDataForRange')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">{t('common.date')}</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">{t('dashboard.revenue')}</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">{t('inventory.deliveries')}</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">{t('reports.spoilage')}</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">{t('dashboard.profit')}</th>
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
  const { t } = useTranslation()
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
  if (error) return <div className="card text-red-600">{t('errors.generic')}</div>

  return (
    <div className="space-y-6">
      {/* Ingredient Filter */}
      {ingredientsData && ingredientsData.items.length > 0 && (
        <div className="card">
          <h4 className="text-sm font-medium text-gray-700 mb-2">{t('reports.filterIngredients')}</h4>
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
                {t('common.clearFilters')}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Summary */}
      {data && data.summary.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('reports.usageSummary')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.summary.map((item) => (
              <div key={item.ingredient_id} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">{item.ingredient_name}</p>
                <p className="text-xl font-bold text-gray-900">
                  {Number(item.total_used).toFixed(item.unit_label === 'szt' ? 0 : 2)} {item.unit_label}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{t('reports.usageDetails')}</h3>
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
            {t('common.exportToExcel')}
          </button>
        </div>

        {!data?.items.length ? (
          <p className="text-gray-500 text-center py-8">{t('reports.noDataForRange')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-700">{t('common.date')}</th>
                  <th className="text-left py-3 px-2 font-medium text-gray-700">{t('menu.ingredient')}</th>
                  <th className="text-right py-3 px-2 font-medium text-gray-700">{t('reports.openQty')}</th>
                  <th className="text-right py-3 px-2 font-medium text-green-600">+{t('inventory.deliveries')}</th>
                  <th className="text-right py-3 px-2 font-medium text-blue-600">+{t('inventory.transfers')}</th>
                  <th className="text-right py-3 px-2 font-medium text-red-600">-{t('reports.spoilage')}</th>
                  <th className="text-right py-3 px-2 font-medium text-orange-600">-{t('inventory.usage')}</th>
                  <th className="text-right py-3 px-2 font-medium text-gray-900">{t('reports.closeQty')}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item, index) => {
                  const decimals = item.unit_label === 'szt' ? 0 : 2
                  const opening = Number(item.opening)
                  const deliveries = Number(item.deliveries)
                  const transfers = Number(item.transfers)
                  const spoilage = Number(item.spoilage)
                  const usage = Number(item.usage)
                  const closing = Number(item.closing)

                  return (
                    <tr key={`${item.date}-${item.ingredient_id}-${index}`} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-2">{formatDate(item.date)}</td>
                      <td className="py-2 px-2 font-medium">{item.ingredient_name}</td>
                      <td className="py-2 px-2 text-right">
                        {opening.toFixed(decimals)}
                      </td>
                      <td className="py-2 px-2 text-right text-green-600">
                        {deliveries > 0 ? `+${deliveries.toFixed(decimals)}` : '-'}
                      </td>
                      <td className="py-2 px-2 text-right text-blue-600">
                        {transfers > 0 ? `+${transfers.toFixed(decimals)}` : '-'}
                      </td>
                      <td className="py-2 px-2 text-right text-red-600">
                        {spoilage > 0 ? `-${spoilage.toFixed(decimals)}` : '-'}
                      </td>
                      <td className="py-2 px-2 text-right text-orange-600 font-medium">
                        -{usage.toFixed(decimals)}
                      </td>
                      <td className="py-2 px-2 text-right font-bold">
                        {closing.toFixed(decimals)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {/* Legend */}
            <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500">
              <p className="font-medium mb-1">{t('reports.formula')}:</p>
              <p>{t('reports.openQty')} + {t('inventory.deliveries')} + {t('inventory.transfers')} - {t('reports.spoilage')} - {t('inventory.usage')} = {t('reports.closeQty')}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function SpoilageReportSection({ dateRange, isExporting, setIsExporting }: ReportSectionProps) {
  const { t } = useTranslation()

  const SPOILAGE_REASON_LABELS: Record<SpoilageReason, string> = {
    expired: t('spoilageModal.reasons.expired'),
    over_prepared: t('spoilageModal.reasons.overPrepared'),
    contaminated: t('spoilageModal.reasons.contaminated'),
    equipment_failure: t('spoilageModal.reasons.equipmentFailure'),
    other: t('spoilageModal.reasons.other'),
  }

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
  if (error) return <div className="card text-red-600">{t('errors.generic')}</div>

  return (
    <div className="space-y-6">
      {/* Summary by Reason */}
      {data && data.by_reason && data.by_reason.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('reports.summaryByReason')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.by_reason.map((item) => (
              <div key={item.reason} className="p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-gray-500">{item.reason_label || SPOILAGE_REASON_LABELS[item.reason]}</p>
                <p className="text-xl font-bold text-red-600">{item.total_count} {t('common.items')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary by Ingredient */}
      {data && data.by_ingredient && data.by_ingredient.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('reports.summaryByIngredient')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.by_ingredient.map((item) => (
              <div key={item.ingredient_id} className="p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-gray-500">{item.ingredient_name}</p>
                <p className="text-xl font-bold text-orange-600">
                  {Number(item.total_quantity).toFixed(item.unit_label === 'szt' ? 0 : 2)} {item.unit_label}
                </p>
                <p className="text-sm text-gray-400">{item.total_count} {t('reports.cases')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{t('reports.spoilageList')}</h3>
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
            {t('common.exportToExcel')}
          </button>
        </div>

        {!data?.items.length ? (
          <p className="text-gray-500 text-center py-8">{t('reports.noDataForRange')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">{t('common.date')}</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">{t('menu.ingredient')}</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">{t('closeDayModal.quantity')}</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">{t('spoilageModal.reason')}</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">{t('reports.notes')}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item, index) => (
                  <tr key={`${item.date}-${item.ingredient_id}-${index}`} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">{formatDate(item.date)}</td>
                    <td className="py-3 px-4">{item.ingredient_name}</td>
                    <td className="py-3 px-4 text-right font-medium text-red-600">
                      {Number(item.quantity).toFixed(item.unit_label === 'szt' ? 0 : 2)} {item.unit_label}
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
