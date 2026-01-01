import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Truck, Package, Trash2, X } from 'lucide-react'
import LoadingSpinner from '../common/LoadingSpinner'
import ConfirmDialog from '../common/ConfirmDialog'
import { useToast } from '../../context/ToastContext'
import {
  getDeliveries,
  deleteDelivery,
  getTransfers,
  deleteTransfer,
  getSpoilage,
  deleteSpoilage,
} from '../../api/midDayOperations'
import { formatCurrency, formatDateTime, formatQuantity } from '../../utils/formatters'
import type { Delivery, StorageTransfer, Spoilage, SpoilageReason } from '../../types'

interface MidDayEventsListProps {
  dailyRecordId: number
}

// Spoilage reason labels in Polish
const SPOILAGE_REASON_LABELS: Record<SpoilageReason, string> = {
  expired: 'Przeterminowane',
  damaged: 'Uszkodzone',
  quality: 'Jakosc',
  other: 'Inne',
}

type DeleteType = 'delivery' | 'transfer' | 'spoilage'

interface DeleteConfirmState {
  isOpen: boolean
  type: DeleteType | null
  id: number | null
  name: string
}

export default function MidDayEventsList({ dailyRecordId }: MidDayEventsListProps) {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  // Confirm dialog state
  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmState>({
    isOpen: false,
    type: null,
    id: null,
    name: '',
  })

  // Fetch deliveries
  const { data: deliveries, isLoading: deliveriesLoading } = useQuery({
    queryKey: ['deliveries', dailyRecordId],
    queryFn: () => getDeliveries(dailyRecordId),
  })

  // Fetch transfers
  const { data: transfers, isLoading: transfersLoading } = useQuery({
    queryKey: ['transfers', dailyRecordId],
    queryFn: () => getTransfers(dailyRecordId),
  })

  // Fetch spoilage
  const { data: spoilageList, isLoading: spoilageLoading } = useQuery({
    queryKey: ['spoilage', dailyRecordId],
    queryFn: () => getSpoilage(dailyRecordId),
  })

  // Delete mutations
  const deleteDeliveryMutation = useMutation({
    mutationFn: deleteDelivery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
      showSuccess('Dostawa zostala usunieta')
      closeDeleteConfirm()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      showError(error.response?.data?.detail || 'Wystapil blad podczas usuwania dostawy')
      closeDeleteConfirm()
    },
  })

  const deleteTransferMutation = useMutation({
    mutationFn: deleteTransfer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfers', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
      showSuccess('Transfer zostal usuniety')
      closeDeleteConfirm()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      showError(error.response?.data?.detail || 'Wystapil blad podczas usuwania transferu')
      closeDeleteConfirm()
    },
  })

  const deleteSpoilageMutation = useMutation({
    mutationFn: deleteSpoilage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['spoilage', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
      showSuccess('Wpis o stracie zostal usuniety')
      closeDeleteConfirm()
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      showError(error.response?.data?.detail || 'Wystapil blad podczas usuwania wpisu o stracie')
      closeDeleteConfirm()
    },
  })

  // Open delete confirmation
  const openDeleteConfirm = (type: DeleteType, id: number, name: string) => {
    setDeleteConfirm({ isOpen: true, type, id, name })
  }

  const closeDeleteConfirm = () => {
    setDeleteConfirm({ isOpen: false, type: null, id: null, name: '' })
  }

  // Handle confirmed delete
  const handleConfirmDelete = () => {
    if (!deleteConfirm.id || !deleteConfirm.type) return

    switch (deleteConfirm.type) {
      case 'delivery':
        deleteDeliveryMutation.mutate(deleteConfirm.id)
        break
      case 'transfer':
        deleteTransferMutation.mutate(deleteConfirm.id)
        break
      case 'spoilage':
        deleteSpoilageMutation.mutate(deleteConfirm.id)
        break
    }
  }

  const getDeleteDialogContent = () => {
    switch (deleteConfirm.type) {
      case 'delivery':
        return {
          title: 'Usun dostawe',
          message: `Czy na pewno chcesz usunac dostawe "${deleteConfirm.name}"? Ta operacja jest nieodwracalna.`,
        }
      case 'transfer':
        return {
          title: 'Usun transfer',
          message: `Czy na pewno chcesz usunac transfer "${deleteConfirm.name}"? Ta operacja jest nieodwracalna.`,
        }
      case 'spoilage':
        return {
          title: 'Usun wpis o stracie',
          message: `Czy na pewno chcesz usunac wpis o stracie "${deleteConfirm.name}"? Ta operacja jest nieodwracalna.`,
        }
      default:
        return { title: '', message: '' }
    }
  }

  const isDeleting =
    deleteDeliveryMutation.isPending ||
    deleteTransferMutation.isPending ||
    deleteSpoilageMutation.isPending

  const isLoading = deliveriesLoading || transfersLoading || spoilageLoading
  const hasDeliveries = deliveries && deliveries.length > 0
  const hasTransfers = transfers && transfers.length > 0
  const hasSpoilage = spoilageList && spoilageList.length > 0
  const hasAnyEvents = hasDeliveries || hasTransfers || hasSpoilage

  const dialogContent = getDeleteDialogContent()

  if (isLoading) {
    return (
      <div className="card">
        <h3 className="card-header">Dzisiejsze zdarzenia</h3>
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="card">
        <h3 className="card-header">Dzisiejsze zdarzenia</h3>

        {!hasAnyEvents ? (
          <div className="empty-state">
            <p className="empty-state-title">Brak zdarzen</p>
            <p className="empty-state-description">
              Dodaj dostawy, transfery lub straty korzystajac z przyciskow powyzej.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Deliveries section */}
            {hasDeliveries && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Truck className="w-5 h-5 text-green-600" />
                  <h4 className="font-medium text-gray-900">Dostawy</h4>
                  <span className="px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">
                    {deliveries.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {deliveries.map((delivery: Delivery) => (
                    <div
                      key={delivery.id}
                      className="flex items-center justify-between p-3 bg-green-50 rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-gray-900">
                            {delivery.ingredient_name}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatQuantity(delivery.quantity, delivery.unit_label === 'kg' ? 'weight' : 'count')}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500 flex-wrap">
                          <span>{formatCurrency(delivery.price_pln)}</span>
                          <span>{formatDateTime(delivery.delivered_at)}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => openDeleteConfirm('delivery', delivery.id, delivery.ingredient_name)}
                        disabled={isDeleting}
                        className="p-2 hover:bg-red-100 rounded-lg transition-colors flex-shrink-0"
                        title="Usun dostawe"
                        aria-label={`Usun dostawe ${delivery.ingredient_name}`}
                      >
                        <X className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transfers section */}
            {hasTransfers && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Package className="w-5 h-5 text-blue-600" />
                  <h4 className="font-medium text-gray-900">Transfery z magazynu</h4>
                  <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">
                    {transfers.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {transfers.map((transfer: StorageTransfer) => (
                    <div
                      key={transfer.id}
                      className="flex items-center justify-between p-3 bg-blue-50 rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-gray-900">
                            {transfer.ingredient_name}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatQuantity(transfer.quantity, transfer.unit_label === 'kg' ? 'weight' : 'count')}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          {formatDateTime(transfer.transferred_at)}
                        </div>
                      </div>
                      <button
                        onClick={() => openDeleteConfirm('transfer', transfer.id, transfer.ingredient_name)}
                        disabled={isDeleting}
                        className="p-2 hover:bg-red-100 rounded-lg transition-colors flex-shrink-0"
                        title="Usun transfer"
                        aria-label={`Usun transfer ${transfer.ingredient_name}`}
                      >
                        <X className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Spoilage section */}
            {hasSpoilage && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Trash2 className="w-5 h-5 text-red-600" />
                  <h4 className="font-medium text-gray-900">Straty</h4>
                  <span className="px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded-full">
                    {spoilageList.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {spoilageList.map((spoilage: Spoilage) => (
                    <div
                      key={spoilage.id}
                      className="flex items-center justify-between p-3 bg-red-50 rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-gray-900">
                            {spoilage.ingredient_name}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatQuantity(spoilage.quantity, spoilage.unit_label === 'kg' ? 'weight' : 'count')}
                          </span>
                          <span className="px-2 py-0.5 text-xs bg-red-200 text-red-800 rounded">
                            {SPOILAGE_REASON_LABELS[spoilage.reason]}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500 flex-wrap">
                          <span>{formatDateTime(spoilage.recorded_at)}</span>
                          {spoilage.notes && (
                            <span className="italic truncate max-w-xs">"{spoilage.notes}"</span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => openDeleteConfirm('spoilage', spoilage.id, spoilage.ingredient_name)}
                        disabled={isDeleting}
                        className="p-2 hover:bg-red-200 rounded-lg transition-colors flex-shrink-0"
                        title="Usun strate"
                        aria-label={`Usun strate ${spoilage.ingredient_name}`}
                      >
                        <X className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        isOpen={deleteConfirm.isOpen}
        onClose={closeDeleteConfirm}
        onConfirm={handleConfirmDelete}
        title={dialogContent.title}
        message={dialogContent.message}
        confirmText="Usun"
        cancelText="Anuluj"
        variant="danger"
        isLoading={isDeleting}
      />
    </>
  )
}
