import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { DollarSign, Clock, TrendingUp, TrendingDown, Users, Calendar } from 'lucide-react'
import { getWageAnalytics } from '../../api/wageAnalytics'
import { getEmployees } from '../../api/employees'
import { formatCurrency } from '../../utils/formatters'
import LoadingSpinner from '../common/LoadingSpinner'

export default function WageAnalyticsSection() {
  const { t } = useTranslation()
  const currentDate = new Date()
  const [month, setMonth] = useState(currentDate.getMonth() + 1)
  const [year, setYear] = useState(currentDate.getFullYear())
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | undefined>()

  const { data: employeesData } = useQuery({
    queryKey: ['employees', { includeInactive: true }],
    queryFn: () => getEmployees(true),
  })

  const { data: analyticsData, isLoading, error } = useQuery({
    queryKey: ['wageAnalytics', { month, year, employee_id: selectedEmployeeId }],
    queryFn: () => getWageAnalytics({ month, year, employee_id: selectedEmployeeId }),
    enabled: !!month && !!year,
  })

  const months = [
    { value: 1, label: t('months.january') },
    { value: 2, label: t('months.february') },
    { value: 3, label: t('months.march') },
    { value: 4, label: t('months.april') },
    { value: 5, label: t('months.may') },
    { value: 6, label: t('months.june') },
    { value: 7, label: t('months.july') },
    { value: 8, label: t('months.august') },
    { value: 9, label: t('months.september') },
    { value: 10, label: t('months.october') },
    { value: 11, label: t('months.november') },
    { value: 12, label: t('months.december') },
  ]

  const years = Array.from({ length: 5 }, (_, i) => currentDate.getFullYear() - i)

  const getChangeIcon = (changePercent: number | null) => {
    if (changePercent === null) return null
    if (changePercent > 0) {
      return <TrendingUp className="w-4 h-4 text-red-500" />
    } else if (changePercent < 0) {
      return <TrendingDown className="w-4 h-4 text-green-500" />
    }
    return null
  }

  const getChangeColor = (changePercent: number | null) => {
    if (changePercent === null) return 'text-gray-500'
    if (changePercent > 0) return 'text-red-600'
    if (changePercent < 0) return 'text-green-600'
    return 'text-gray-600'
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">{t('employees.period')}:</span>
          </div>
          <select
            value={month}
            onChange={(e) => setMonth(parseInt(e.target.value))}
            className="input w-auto"
          >
            {months.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
          <select
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
            className="input w-auto"
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>

          <div className="flex items-center gap-2 ml-4">
            <Users className="w-5 h-5 text-gray-500" />
            <select
              value={selectedEmployeeId || ''}
              onChange={(e) =>
                setSelectedEmployeeId(e.target.value ? parseInt(e.target.value) : undefined)
              }
              className="input w-auto"
            >
              <option value="">{t('employees.allEmployees')}</option>
              {employeesData?.items.map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="card text-red-600">{t('errors.generic')}</div>
      ) : analyticsData ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-primary-100 rounded-lg">
                  <DollarSign className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{t('employees.totalWages')}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(analyticsData.summary.total_wages)}
                  </p>
                  {analyticsData.previous_month_summary && (
                    <p className="text-sm text-gray-500">
                      {t('employees.previousMonth')}: {formatCurrency(analyticsData.previous_month_summary.total_wages)}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Clock className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{t('employees.totalHoursWorked')}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.summary.total_hours.toFixed(1)} h
                  </p>
                  {analyticsData.previous_month_summary && (
                    <p className="text-sm text-gray-500">
                      {t('employees.previousMonth')}: {analyticsData.previous_month_summary.total_hours.toFixed(1)} h
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-amber-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{t('employees.avgCostPerHour')}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(analyticsData.summary.avg_cost_per_hour)}/h
                  </p>
                  {analyticsData.previous_month_summary && (
                    <p className="text-sm text-gray-500">
                      {t('employees.previousMonth')}: {formatCurrency(analyticsData.previous_month_summary.avg_cost_per_hour)}/h
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Employee Breakdown Table */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {t('employees.breakdownByEmployee')}
            </h3>

            {analyticsData.by_employee.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                {t('employees.noDataForPeriod')}
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                        {t('employees.employee')}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                        {t('employees.position')}
                      </th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                        {t('employees.hours')}
                      </th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                        {t('employees.wages')}
                      </th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                        {t('employees.costPerHour')}
                      </th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                        {t('employees.changeVsPrevious')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {analyticsData.by_employee.map((employee) => (
                      <tr key={employee.employee_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-gray-900">
                          {employee.employee_name}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {employee.position_name}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-900">
                          {employee.hours_worked.toFixed(1)} h
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900">
                          {formatCurrency(employee.wages_paid)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-600">
                          {formatCurrency(employee.cost_per_hour)}/h
                        </td>
                        <td className="px-4 py-3 text-right">
                          {employee.change_percent !== null ? (
                            <div className="flex items-center justify-end gap-1">
                              {getChangeIcon(employee.change_percent)}
                              <span className={getChangeColor(employee.change_percent)}>
                                {employee.change_percent > 0 ? '+' : ''}
                                {employee.change_percent.toFixed(1)}%
                              </span>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="card text-gray-500 text-center py-8">
          {t('employees.selectPeriodToViewAnalytics')}
        </div>
      )}
    </div>
  )
}
