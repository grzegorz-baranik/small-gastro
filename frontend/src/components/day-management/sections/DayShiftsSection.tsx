import { useTranslation } from 'react-i18next'
import { Users } from 'lucide-react'
import ShiftAssignmentSection from '../../employees/ShiftAssignmentSection'

interface DayShiftsSectionProps {
  dayId: number
  isEditable: boolean
}

export default function DayShiftsSection({ dayId, isEditable }: DayShiftsSectionProps) {
  const { t } = useTranslation()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Users className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold text-gray-900">
          {t('employees.shifts')}
        </h3>
      </div>

      {/* Shift Assignment Section */}
      <ShiftAssignmentSection
        dailyRecordId={dayId}
        isEditable={isEditable}
      />
    </div>
  )
}
