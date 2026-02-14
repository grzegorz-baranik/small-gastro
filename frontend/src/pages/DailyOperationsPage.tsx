import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  Play,
  Square,
  Settings,
  AlertTriangle,
  CheckCircle,
  Calendar,
  Clock,
} from 'lucide-react'
import { useDailyRecord } from '../context/DailyRecordContext'
import { getRecentDays } from '../api/dailyOperations'
import { formatCurrency, formatDate, getTodayDateString } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { OpenDayModal, CloseDayWizard } from '../components/daily'
import type { DailyRecord, RecentDayRecord } from '../types'

export default function DailyOperationsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { todayRecord, openRecord, isDayOpen, isLoading: recordLoading, refetch } = useDailyRecord()
  const queryClient = useQueryClient()

  // Modal states
  const [openDayModalOpen, setOpenDayModalOpen] = useState(false)
  const [closeDayModalOpen, setCloseDayModalOpen] = useState(false)
  const [recordToClose, setRecordToClose] = useState<DailyRecord | null>(null)

  // Fetch recent days
  const { data: recentDays, isLoading: recentDaysLoading } = useQuery({
    queryKey: ['recentDays'],
    queryFn: () => getRecentDays(7),
  })

  // Get day of week name
  const getDayName = (dateString: string): string => {
    const date = new Date(dateString)
    const dayKeys = [
      'sunday',
      'monday',
      'tuesday',
      'wednesday',
      'thursday',
      'friday',
      'saturday',
    ]
    return t(`dailyOperations.dayOfWeek.${dayKeys[date.getDay()]}`)
  }

  // Get status badge
  const getStatusBadge = (status: string) => {
    if (status === 'open') {
      return (
        <span data-testid="day-status-badge" className="px-3 py-1 text-sm font-medium bg-green-100 text-green-800 rounded-full">
          {t('dailyOperations.statusOpen')}
        </span>
      )
    }
    return (
      <span data-testid="day-status-badge" className="px-3 py-1 text-sm font-medium bg-gray-100 text-gray-800 rounded-full">
        {t('dailyOperations.statusClosed')}
      </span>
    )
  }

  // Handle success callbacks
  const handleOpenDaySuccess = () => {
    refetch()
    queryClient.invalidateQueries({ queryKey: ['recentDays'] })
  }

  const handleCloseDaySuccess = () => {
    refetch()
    queryClient.invalidateQueries({ queryKey: ['recentDays'] })
  }

  // Navigation handlers
  const handleManageDay = (dayId: number) => {
    navigate(`/operacje/${dayId}`)
  }

  const handleRowClick = (day: RecentDayRecord) => {
    navigate(`/operacje/${day.id}`)
  }

  if (recordLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  const today = getTodayDateString()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('dailyOperations.title')}</h1>
      </div>

      {/* Warning banner - open day is not today */}
      {isDayOpen && openRecord && openRecord.date !== today && (
        <div className="card bg-amber-50 border-amber-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <AlertTriangle className="w-8 h-8 text-amber-600" />
              <div>
                <h2 className="text-lg font-semibold text-amber-800">
                  {t('dailyOperations.openDayLabel')}: {formatDate(openRecord.date)} ({getDayName(openRecord.date)})
                </h2>
                {openRecord.opened_at && (
                  <p className="text-sm text-amber-600 flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {t('dailyOperations.openedAt')} {new Date(openRecord.opened_at).toLocaleTimeString('pl-PL', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={() => handleManageDay(openRecord.id)}
              className="btn btn-primary flex items-center gap-2"
              data-testid="manage-day-btn"
            >
              <Settings className="w-5 h-5" />
              {t('dailyOperations.manageDay')}
            </button>
          </div>
        </div>
      )}

      {/* Today's status card */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Calendar className="w-8 h-8 text-primary-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {t('dailyOperations.todayLabel')} {formatDate(today)} ({getDayName(today)})
              </h2>
              {todayRecord?.opened_at && (
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {t('dailyOperations.openedAt')} {new Date(todayRecord.opened_at).toLocaleTimeString('pl-PL', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              )}
            </div>
          </div>
          <div>
            {todayRecord ? getStatusBadge(todayRecord.status) : (
              <span className="px-3 py-1 text-sm font-medium bg-yellow-100 text-yellow-800 rounded-full">
                {t('dailyOperations.statusNotOpened')}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={() => setOpenDayModalOpen(true)}
            disabled={isDayOpen}
            data-testid="open-day-btn"
            className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
              isDayOpen
                ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                : 'border-primary-200 bg-primary-50 text-primary-700 hover:bg-primary-100 hover:border-primary-300'
            }`}
          >
            <Play className="w-8 h-8" />
            <span className="font-medium">{t('dailyOperations.openDay')}</span>
          </button>

          <button
            onClick={() => openRecord && handleManageDay(openRecord.id)}
            disabled={!isDayOpen}
            data-testid="manage-day-btn"
            className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
              !isDayOpen
                ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                : 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300'
            }`}
          >
            <Settings className="w-8 h-8" />
            <span className="font-medium">{t('dailyOperations.manageDay')}</span>
          </button>

          <button
            onClick={() => {
              if (openRecord) {
                setRecordToClose(openRecord)
                setCloseDayModalOpen(true)
              }
            }}
            disabled={!isDayOpen}
            data-testid="close-day-btn"
            className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
              !isDayOpen
                ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                : 'border-orange-200 bg-orange-50 text-orange-700 hover:bg-orange-100 hover:border-orange-300'
            }`}
          >
            <Square className="w-8 h-8" />
            <span className="font-medium">{t('dailyOperations.closeDay')}</span>
          </button>
        </div>
      </div>

      {/* Recent days history */}
      <div className="card">
        <h3 className="card-header">{t('dailyOperations.recentDays')}</h3>
        {recentDaysLoading ? (
          <LoadingSpinner />
        ) : recentDays && recentDays.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="recent-days-table">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                    {t('common.date')}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                    {t('common.status')}
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                    {t('dailyOperations.income')}
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">
                    {t('dailyOperations.alerts')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recentDays.map((day: RecentDayRecord) => (
                  <tr
                    key={day.id}
                    onClick={() => handleRowClick(day)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">
                        {formatDate(day.date)}
                      </div>
                      <div className="text-sm text-gray-500">
                        {getDayName(day.date)}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {day.status === 'open' ? (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                          <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5"></span>
                          {t('dailyOperations.statusOpen')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                          {t('dailyOperations.statusClosed')}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      {day.total_income_pln !== null
                        ? formatCurrency(day.total_income_pln)
                        : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {day.alerts_count > 0 ? (
                        <span className="inline-flex items-center gap-1 text-yellow-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm">
                            {day.alerts_count} {day.alerts_count === 1 ? t('dailyOperations.warningCount') : t('dailyOperations.warningsCount')}
                          </span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-green-600">
                          <CheckCircle className="w-4 h-4" />
                          <span className="text-sm">{t('common.ok')}</span>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">{t('dailyOperations.noHistory')}</p>
        )}
      </div>

      {/* Modals */}
      <OpenDayModal
        isOpen={openDayModalOpen}
        onClose={() => setOpenDayModalOpen(false)}
        onSuccess={handleOpenDaySuccess}
      />

      {recordToClose && (
        <CloseDayWizard
          isOpen={closeDayModalOpen}
          onClose={() => {
            setCloseDayModalOpen(false)
            setRecordToClose(null)
          }}
          onSuccess={handleCloseDaySuccess}
          dailyRecord={recordToClose}
        />
      )}
    </div>
  )
}
