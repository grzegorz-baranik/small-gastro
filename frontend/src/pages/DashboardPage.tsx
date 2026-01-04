import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { getDashboardOverview, getDiscrepancyWarnings } from '../api/dashboard'
import { formatCurrency } from '../utils/formatters'
import { TrendingUp, TrendingDown, Wallet, AlertTriangle } from 'lucide-react'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function DashboardPage() {
  const { t } = useTranslation()
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboardOverview'],
    queryFn: getDashboardOverview,
  })

  const { data: warnings } = useQuery({
    queryKey: ['discrepancyWarnings'],
    queryFn: () => getDiscrepancyWarnings(7),
  })

  if (overviewLoading) {
    return <LoadingSpinner size="lg" />
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.title')}</h1>

      {/* Today's Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{t('dashboard.todayRevenue')}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(overview?.today_revenue ?? 0)}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{t('dashboard.todayExpenses')}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(overview?.today_expenses ?? 0)}
              </p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <TrendingDown className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{t('dashboard.todayProfit')}</p>
              <p className={`text-2xl font-bold mt-1 ${(overview?.today_profit ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(overview?.today_profit ?? 0)}
              </p>
            </div>
            <div className="p-3 bg-primary-100 rounded-lg">
              <Wallet className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Period Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="card-header">{t('dashboard.thisWeek')}</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">{t('dashboard.revenue')}</span>
              <span className="font-medium">{formatCurrency(overview?.week_revenue ?? 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('dashboard.expenses')}</span>
              <span className="font-medium">{formatCurrency(overview?.week_expenses ?? 0)}</span>
            </div>
            <div className="flex justify-between border-t pt-3">
              <span className="font-medium">{t('dashboard.profit')}</span>
              <span className={`font-bold ${(overview?.week_profit ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(overview?.week_profit ?? 0)}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="card-header">{t('dashboard.thisMonth')}</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">{t('dashboard.revenue')}</span>
              <span className="font-medium">{formatCurrency(overview?.month_revenue ?? 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('dashboard.expenses')}</span>
              <span className="font-medium">{formatCurrency(overview?.month_expenses ?? 0)}</span>
            </div>
            <div className="flex justify-between border-t pt-3">
              <span className="font-medium">{t('dashboard.profit')}</span>
              <span className={`font-bold ${(overview?.month_profit ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(overview?.month_profit ?? 0)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <h2 className="card-header mb-0">{t('dashboard.discrepancyWarnings')}</h2>
          </div>
          <div className="space-y-3">
            {warnings.slice(0, 5).map((warning) => (
              <div
                key={warning.id}
                className={`p-3 rounded-lg ${
                  warning.severity === 'high'
                    ? 'bg-red-50 border border-red-200'
                    : warning.severity === 'medium'
                    ? 'bg-yellow-50 border border-yellow-200'
                    : 'bg-gray-50 border border-gray-200'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{warning.ingredient_name}</p>
                    <p className="text-sm text-gray-600">
                      {t('dashboard.difference')}: {warning.discrepancy.toFixed(2)} ({warning.discrepancy_percent.toFixed(1)}%)
                    </p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded ${
                    warning.severity === 'high'
                      ? 'bg-red-100 text-red-700'
                      : warning.severity === 'medium'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}>
                    {warning.severity === 'high'
                      ? t('dashboard.severityHigh')
                      : warning.severity === 'medium'
                      ? t('dashboard.severityMedium')
                      : t('dashboard.severityLow')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
