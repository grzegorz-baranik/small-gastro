import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Briefcase } from 'lucide-react'
import { getPositions, createPosition, updatePosition, deletePosition } from '../../api/positions'
import { formatCurrency } from '../../utils/formatters'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import type { Position, PositionCreate, PositionUpdate } from '../../types'

export default function PositionsSection() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editingPosition, setEditingPosition] = useState<Position | null>(null)

  const { data: positionsData, isLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: getPositions,
  })

  const createMutation = useMutation({
    mutationFn: createPosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setShowModal(false)
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PositionUpdate }) => updatePosition(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setEditingPosition(null)
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deletePosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] })
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || t('errors.generic')
      alert(message)
    },
  })

  const handleDelete = (position: Position) => {
    if (position.employee_count > 0) {
      alert(t('employees.errors.positionHasEmployees'))
      return
    }
    if (window.confirm(t('employees.confirmDeletePosition'))) {
      deleteMutation.mutate(position.id)
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-primary-600" />
          <h2 className="card-header mb-0">{t('employees.positions')}</h2>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          {t('employees.addPosition')}
        </button>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : positionsData?.items.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          {t('employees.noPositions')}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                  {t('common.name')}
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                  {t('employees.hourlyRate')}
                </th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">
                  {t('employees.employeeCount')}
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {positionsData?.items.map((position) => (
                <tr key={position.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {position.name}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900">
                    {formatCurrency(position.hourly_rate)}/h
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded-full">
                      {position.employee_count}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setEditingPosition(position)}
                        className="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-gray-700"
                        title={t('common.edit')}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(position)}
                        className="p-1 hover:bg-red-100 rounded text-gray-500 hover:text-red-600"
                        title={t('common.delete')}
                        disabled={position.employee_count > 0}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Position Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={t('employees.addPosition')}
      >
        <PositionForm
          onSubmit={(data) => createMutation.mutate(data as PositionCreate)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Position Modal */}
      <Modal
        isOpen={!!editingPosition}
        onClose={() => setEditingPosition(null)}
        title={t('employees.editPosition')}
      >
        {editingPosition && (
          <PositionForm
            initialData={editingPosition}
            onSubmit={(data) => updateMutation.mutate({ id: editingPosition.id, data })}
            isLoading={updateMutation.isPending}
          />
        )}
      </Modal>
    </div>
  )
}

function PositionForm({
  initialData,
  onSubmit,
  isLoading,
}: {
  initialData?: Position
  onSubmit: (data: PositionCreate | PositionUpdate) => void
  isLoading: boolean
}) {
  const { t } = useTranslation()
  const [name, setName] = useState(initialData?.name || '')
  const [hourlyRate, setHourlyRate] = useState(initialData?.hourly_rate?.toString() || '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isLoading || !name.trim() || !hourlyRate) return
    onSubmit({
      name: name.trim(),
      hourly_rate: parseFloat(hourlyRate),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {t('common.name')}
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="input"
          placeholder={t('employees.positionNamePlaceholder')}
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {t('employees.hourlyRate')} (PLN)
        </label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={hourlyRate}
          onChange={(e) => setHourlyRate(e.target.value)}
          className="input"
          placeholder="25.00"
          required
        />
      </div>

      <button type="submit" className="btn btn-primary w-full" disabled={isLoading}>
        {isLoading ? t('common.saving') : t('common.save')}
      </button>
    </form>
  )
}
