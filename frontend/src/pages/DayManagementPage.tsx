import { useState } from 'react'
import { useParams, Navigate, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { getDailyRecord } from '../api/dailyOperations'
import { DaySidebarNav, type DaySection } from '../components/day-management'
import {
  DayOverviewSection,
  DayOpeningSection,
  DayShiftsSection,
  DayOperationsSection,
  DaySalesSection,
  DayClosingSection,
} from '../components/day-management/sections'

export default function DayManagementPage() {
  const { t } = useTranslation()
  const { dayId } = useParams<{ dayId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [currentSection, setCurrentSection] = useState<DaySection>('overview')

  const recordId = dayId ? parseInt(dayId, 10) : null

  const {
    data: dailyRecord,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['dailyRecord', recordId],
    queryFn: () => getDailyRecord(recordId!),
    enabled: recordId !== null && !isNaN(recordId),
  })

  // Determine if day is editable (only open days can be edited)
  const isEditable = dailyRecord?.status === 'open'

  // Handler for when day is closed
  const handleDayClosed = () => {
    queryClient.invalidateQueries({ queryKey: ['dailyRecord'] })
    navigate('/operacje')
  }

  // Invalid dayId parameter
  if (!recordId || isNaN(recordId)) {
    return <Navigate to="/operacje" replace />
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  // Error state / 404
  if (isError || !dailyRecord) {
    const is404 = (error as { response?: { status?: number } })?.response?.status === 404

    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900">
            {is404 ? t('dayManagement.notFound') : t('dayManagement.loadError')}
          </h2>
          <p className="mt-2 text-gray-600">
            {is404
              ? t('dayManagement.notFoundDescription')
              : t('dayManagement.loadErrorDescription')}
          </p>
          <button
            onClick={() => window.history.back()}
            className="mt-4 btn btn-primary"
          >
            {t('dayManagement.backToList')}
          </button>
        </div>
      </div>
    )
  }

  const handleSectionChange = (section: DaySection) => {
    setCurrentSection(section)
  }

  // Render the appropriate section component
  const renderSectionContent = () => {
    // recordId is guaranteed to be a valid number at this point (checked above)
    const numericDayId = recordId!

    switch (currentSection) {
      case 'overview':
        return <DayOverviewSection dayId={numericDayId} />
      case 'opening':
        return <DayOpeningSection dayId={numericDayId} isEditable={isEditable} />
      case 'shifts':
        return <DayShiftsSection dayId={numericDayId} isEditable={isEditable} />
      case 'operations':
        return <DayOperationsSection dayId={numericDayId} isEditable={isEditable} />
      case 'sales':
        return <DaySalesSection dayId={numericDayId} isEditable={isEditable} />
      case 'closing':
        return (
          <DayClosingSection
            dayId={numericDayId}
            isEditable={isEditable}
            onDayClosed={handleDayClosed}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="flex h-full -m-6">
      <DaySidebarNav
        currentSection={currentSection}
        onSectionChange={handleSectionChange}
        dayStatus={dailyRecord.status}
        dayDate={dailyRecord.date}
      />
      <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
        {renderSectionContent()}
      </main>
    </div>
  )
}
