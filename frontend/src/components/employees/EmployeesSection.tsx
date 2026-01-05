import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, UserX, UserCheck, Users } from 'lucide-react'
import {
  getEmployees,
  createEmployee,
  updateEmployee,
  deactivateEmployee,
  activateEmployee,
} from '../../api/employees'
import { getPositions } from '../../api/positions'
import { formatCurrency } from '../../utils/formatters'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import type { Employee, EmployeeCreate, EmployeeUpdate, Position } from '../../types'

export default function EmployeesSection() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null)
  const [includeInactive, setIncludeInactive] = useState(false)

  const { data: employeesData, isLoading } = useQuery({
    queryKey: ['employees', { includeInactive }],
    queryFn: () => getEmployees(includeInactive),
  })

  const { data: positionsData } = useQuery({
    queryKey: ['positions'],
    queryFn: getPositions,
  })

  const createMutation = useMutation({
    mutationFn: createEmployee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      setShowModal(false)
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: EmployeeUpdate }) => updateEmployee(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      setEditingEmployee(null)
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: deactivateEmployee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const activateMutation = useMutation({
    mutationFn: activateEmployee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const handleDeactivate = (employee: Employee) => {
    if (window.confirm(t('employees.confirmDeactivate', { name: employee.name }))) {
      deactivateMutation.mutate(employee.id)
    }
  }

  const handleActivate = (employee: Employee) => {
    activateMutation.mutate(employee.id)
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-primary-600" />
          <h2 className="card-header mb-0">{t('employees.employees')}</h2>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            {t('employees.showInactive')}
          </label>
          <button
            onClick={() => setShowModal(true)}
            className="btn btn-primary flex items-center gap-2"
            disabled={!positionsData?.items.length}
          >
            <Plus className="w-4 h-4" />
            {t('employees.addEmployee')}
          </button>
        </div>
      </div>

      {!positionsData?.items.length && (
        <div className="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <p className="text-sm text-yellow-700">
            {t('employees.noPositionsWarning')}
          </p>
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : employeesData?.items.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          {t('employees.noEmployees')}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                  {t('common.name')}
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                  {t('employees.position')}
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                  {t('employees.hourlyRate')}
                </th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">
                  {t('common.status')}
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {employeesData?.items.map((employee) => (
                <tr
                  key={employee.id}
                  className={`hover:bg-gray-50 ${!employee.is_active ? 'opacity-60' : ''}`}
                >
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {employee.name}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {employee.position_name}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900">
                    {formatCurrency(employee.hourly_rate)}/h
                  </td>
                  <td className="px-4 py-3 text-center">
                    {employee.is_active ? (
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
                        {t('employees.statusActive')}
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                        {t('employees.statusInactive')}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setEditingEmployee(employee)}
                        className="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-gray-700"
                        title={t('common.edit')}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      {employee.is_active ? (
                        <button
                          onClick={() => handleDeactivate(employee)}
                          className="p-1 hover:bg-red-100 rounded text-gray-500 hover:text-red-600"
                          title={t('employees.deactivate')}
                        >
                          <UserX className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(employee)}
                          className="p-1 hover:bg-green-100 rounded text-gray-500 hover:text-green-600"
                          title={t('employees.activate')}
                        >
                          <UserCheck className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Employee Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={t('employees.addEmployee')}
      >
        <EmployeeForm
          positions={positionsData?.items || []}
          onSubmit={(data) => createMutation.mutate(data as EmployeeCreate)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Employee Modal */}
      <Modal
        isOpen={!!editingEmployee}
        onClose={() => setEditingEmployee(null)}
        title={t('employees.editEmployee')}
      >
        {editingEmployee && (
          <EmployeeForm
            initialData={editingEmployee}
            positions={positionsData?.items || []}
            onSubmit={(data) => updateMutation.mutate({ id: editingEmployee.id, data })}
            isLoading={updateMutation.isPending}
          />
        )}
      </Modal>
    </div>
  )
}

function EmployeeForm({
  initialData,
  positions,
  onSubmit,
  isLoading,
}: {
  initialData?: Employee
  positions: Position[]
  onSubmit: (data: EmployeeCreate | EmployeeUpdate) => void
  isLoading: boolean
}) {
  const { t } = useTranslation()
  const [name, setName] = useState(initialData?.name || '')
  const [positionId, setPositionId] = useState(initialData?.position_id?.toString() || '')
  const [hourlyRate, setHourlyRate] = useState(initialData?.hourly_rate?.toString() || '')
  const [useCustomRate, setUseCustomRate] = useState(
    initialData ? positions.find(p => p.id === initialData.position_id)?.hourly_rate !== initialData.hourly_rate : false
  )

  const selectedPosition = positions.find(p => p.id === parseInt(positionId))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isLoading || !name.trim() || !positionId) return

    const data: EmployeeCreate | EmployeeUpdate = {
      name: name.trim(),
      position_id: parseInt(positionId),
    }

    if (useCustomRate && hourlyRate) {
      data.hourly_rate = parseFloat(hourlyRate)
    } else {
      data.hourly_rate = null
    }

    onSubmit(data)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {t('employees.employeeName')}
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="input"
          placeholder={t('employees.employeeNamePlaceholder')}
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {t('employees.position')}
        </label>
        <select
          value={positionId}
          onChange={(e) => {
            setPositionId(e.target.value)
            if (!useCustomRate) {
              const pos = positions.find(p => p.id === parseInt(e.target.value))
              if (pos) {
                setHourlyRate(pos.hourly_rate.toString())
              }
            }
          }}
          className="input"
          required
        >
          <option value="">{t('employees.selectPosition')}</option>
          {positions.map((position) => (
            <option key={position.id} value={position.id}>
              {position.name} ({formatCurrency(position.hourly_rate)}/h)
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
          <input
            type="checkbox"
            checked={useCustomRate}
            onChange={(e) => {
              setUseCustomRate(e.target.checked)
              if (!e.target.checked && selectedPosition) {
                setHourlyRate(selectedPosition.hourly_rate.toString())
              }
            }}
            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          {t('employees.useCustomRate')}
        </label>

        <div className="relative">
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={hourlyRate}
            onChange={(e) => setHourlyRate(e.target.value)}
            className="input"
            placeholder={selectedPosition ? selectedPosition.hourly_rate.toString() : '25.00'}
            disabled={!useCustomRate}
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
            PLN/h
          </span>
        </div>
        {!useCustomRate && selectedPosition && (
          <p className="mt-1 text-xs text-gray-500">
            {t('employees.usingPositionRate', { rate: formatCurrency(selectedPosition.hourly_rate) })}
          </p>
        )}
      </div>

      <button type="submit" className="btn btn-primary w-full" disabled={isLoading}>
        {isLoading ? t('common.saving') : t('common.save')}
      </button>
    </form>
  )
}
