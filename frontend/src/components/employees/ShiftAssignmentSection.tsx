import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Clock, Users } from 'lucide-react'
import {
  getShiftAssignments,
  createShiftAssignment,
  updateShiftAssignment,
  deleteShiftAssignment,
} from '../../api/shiftAssignments'
import { getEmployees } from '../../api/employees'
import { formatCurrency } from '../../utils/formatters'
import LoadingSpinner from '../common/LoadingSpinner'
import type { ShiftAssignment, ShiftAssignmentCreate } from '../../types'

interface ShiftAssignmentSectionProps {
  dailyRecordId: number
  isEditable: boolean
}

export default function ShiftAssignmentSection({
  dailyRecordId,
  isEditable,
}: ShiftAssignmentSectionProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [showAddForm, setShowAddForm] = useState(false)
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>('')
  const [startTime, setStartTime] = useState('08:00')
  const [endTime, setEndTime] = useState('16:00')

  const { data: shiftsData, isLoading: shiftsLoading } = useQuery({
    queryKey: ['shifts', dailyRecordId],
    queryFn: () => getShiftAssignments(dailyRecordId),
    enabled: !!dailyRecordId,
  })

  const { data: employeesData } = useQuery({
    queryKey: ['employees', { includeInactive: false }],
    queryFn: () => getEmployees(false),
  })

  // Filter out employees already assigned to this shift
  const availableEmployees = employeesData?.items.filter(
    (employee) => !shiftsData?.items.some((shift) => shift.employee_id === employee.id)
  ) || []

  const createMutation = useMutation({
    mutationFn: (data: ShiftAssignmentCreate) => createShiftAssignment(dailyRecordId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shifts', dailyRecordId] })
      setShowAddForm(false)
      setSelectedEmployeeId('')
      setStartTime('08:00')
      setEndTime('16:00')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ shiftId, start, end }: { shiftId: number; start: string; end: string }) =>
      updateShiftAssignment(dailyRecordId, shiftId, { start_time: start, end_time: end }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shifts', dailyRecordId] })
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (shiftId: number) => deleteShiftAssignment(dailyRecordId, shiftId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shifts', dailyRecordId] })
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const handleAddShift = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedEmployeeId || !startTime || !endTime) return

    createMutation.mutate({
      employee_id: parseInt(selectedEmployeeId),
      start_time: startTime,
      end_time: endTime,
    })
  }

  const handleTimeChange = (shift: ShiftAssignment, field: 'start' | 'end', value: string) => {
    const newStart = field === 'start' ? value : shift.start_time
    const newEnd = field === 'end' ? value : shift.end_time

    updateMutation.mutate({
      shiftId: shift.id,
      start: newStart,
      end: newEnd,
    })
  }

  const totalHours = shiftsData?.items.reduce((sum, shift) => sum + shift.hours_worked, 0) || 0
  const totalWages = shiftsData?.items.reduce(
    (sum, shift) => sum + shift.hours_worked * shift.hourly_rate,
    0
  ) || 0

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-primary-600" />
          <h3 className="card-header mb-0">{t('employees.shifts')}</h3>
        </div>
        {isEditable && availableEmployees.length > 0 && !showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            {t('employees.addToShift')}
          </button>
        )}
      </div>

      {shiftsLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Add employee form */}
          {showAddForm && isEditable && (
            <form
              onSubmit={handleAddShift}
              className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('employees.employee')}
                  </label>
                  <select
                    value={selectedEmployeeId}
                    onChange={(e) => setSelectedEmployeeId(e.target.value)}
                    className="input"
                    required
                  >
                    <option value="">{t('employees.selectEmployee')}</option>
                    {availableEmployees.map((employee) => (
                      <option key={employee.id} value={employee.id}>
                        {employee.name} - {employee.position_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('employees.startTime')}
                  </label>
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('employees.endTime')}
                  </label>
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="input"
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? t('common.saving') : t('common.save')}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="btn btn-secondary"
                >
                  {t('common.cancel')}
                </button>
              </div>
            </form>
          )}

          {/* Shifts list */}
          {shiftsData?.items.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">{t('employees.noShiftsAssigned')}</p>
              {isEditable && availableEmployees.length > 0 && (
                <p className="text-sm text-gray-400 mt-1">
                  {t('employees.addEmployeeToStart')}
                </p>
              )}
            </div>
          ) : (
            <>
              <div className="space-y-2">
                {shiftsData?.items.map((shift) => (
                  <ShiftRow
                    key={shift.id}
                    shift={shift}
                    isEditable={isEditable}
                    onTimeChange={(field, value) => handleTimeChange(shift, field, value)}
                    onDelete={() => {
                      if (window.confirm(t('employees.confirmRemoveFromShift'))) {
                        deleteMutation.mutate(shift.id)
                      }
                    }}
                    isUpdating={updateMutation.isPending}
                  />
                ))}
              </div>

              {/* Summary */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">{t('employees.totalHours')}:</span>
                  <span className="font-medium text-gray-900">{totalHours.toFixed(1)} h</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-500">{t('employees.estimatedWages')}:</span>
                  <span className="font-medium text-gray-900">{formatCurrency(totalWages)}</span>
                </div>
              </div>
            </>
          )}

          {/* Warning if no employees and day is open */}
          {isEditable && shiftsData?.items.length === 0 && (
            <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-sm text-yellow-700">
                {t('employees.noShiftWarning')}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function ShiftRow({
  shift,
  isEditable,
  onTimeChange,
  onDelete,
  isUpdating,
}: {
  shift: ShiftAssignment
  isEditable: boolean
  onTimeChange: (field: 'start' | 'end', value: string) => void
  onDelete: () => void
  isUpdating: boolean
}) {
  const { t } = useTranslation()

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-4">
        <div>
          <p className="font-medium text-gray-900">{shift.employee_name}</p>
          <p className="text-sm text-gray-500">
            {formatCurrency(shift.hourly_rate)}/h
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {isEditable ? (
          <>
            <div className="flex items-center gap-2">
              <input
                type="time"
                value={shift.start_time}
                onChange={(e) => onTimeChange('start', e.target.value)}
                className="input w-28 text-sm"
                disabled={isUpdating}
              />
              <span className="text-gray-400">-</span>
              <input
                type="time"
                value={shift.end_time}
                onChange={(e) => onTimeChange('end', e.target.value)}
                className="input w-28 text-sm"
                disabled={isUpdating}
              />
            </div>
          </>
        ) : (
          <span className="text-gray-600">
            {shift.start_time} - {shift.end_time}
          </span>
        )}

        <div className="text-right min-w-[80px]">
          <p className="font-medium text-gray-900">{shift.hours_worked.toFixed(1)} h</p>
          <p className="text-sm text-gray-500">
            {formatCurrency(shift.hours_worked * shift.hourly_rate)}
          </p>
        </div>

        {isEditable && (
          <button
            onClick={onDelete}
            className="p-2 hover:bg-red-100 rounded-lg transition-colors"
            title={t('employees.removeFromShift')}
          >
            <Trash2 className="w-4 h-4 text-red-600" />
          </button>
        )}
      </div>
    </div>
  )
}
