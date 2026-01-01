import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Truck, Package, Trash2, X } from 'lucide-react'
import LoadingSpinner from '../common/LoadingSpinner'
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

export default function MidDayEventsList({ dailyRecordId }: MidDayEventsListProps) {
  const queryClient = useQueryClient()

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
    },
  })

  const deleteTransferMutation = useMutation({
    mutationFn: deleteTransfer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfers', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
    },
  })

  const deleteSpoilageMutation = useMutation({
    mutationFn: deleteSpoilage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['spoilage', dailyRecordId] })
      queryClient.invalidateQueries({ queryKey: ['dayEvents', dailyRecordId] })
    },
  })

  // Handle delete with confirmation
  const handleDeleteDelivery = (id: number) => {
    if (window.confirm('Czy na pewno chcesz usunac ta dostawe?')) {
      deleteDeliveryMutation.mutate(id)
    }
  }

  const handleDeleteTransfer = (id: number) => {
    if (window.confirm('Czy na pewno chcesz usunac ten transfer?')) {
      deleteTransferMutation.mutate(id)
    }
  }

  const handleDeleteSpoilage = (id: number) => {
    if (window.confirm('Czy na pewno chcesz usunac ten wpis o stracie?')) {
      deleteSpoilageMutation.mutate(id)
    }
  }

  const isLoading = deliveriesLoading || transfersLoading || spoilageLoading
  const hasDeliveries = deliveries && deliveries.length > 0
  const hasTransfers = transfers && transfers.length > 0
  const hasSpoilage = spoilageList && spoilageList.length > 0
  const hasAnyEvents = hasDeliveries || hasTransfers || hasSpoilage

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
    <div className="card">
      <h3 className="card-header">Dzisiejsze zdarzenia</h3>

      {!hasAnyEvents ? (
        <p className="text-gray-500 text-center py-8">
          Brak zdarzen. Dodaj dostawy, transfery lub straty.
        </p>
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
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {delivery.ingredient_name}
                        </span>
                        <span className="text-sm text-gray-500">
                          {formatQuantity(delivery.quantity, delivery.unit_label === 'kg' ? 'weight' : 'count')}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>{formatCurrency(delivery.price_pln)}</span>
                        <span>{formatDateTime(delivery.delivered_at)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteDelivery(delivery.id)}
                      disabled={deleteDeliveryMutation.isPending}
                      className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      title="Usun dostawe"
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
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
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
                      onClick={() => handleDeleteTransfer(transfer.id)}
                      disabled={deleteTransferMutation.isPending}
                      className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      title="Usun transfer"
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
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
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
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>{formatDateTime(spoilage.recorded_at)}</span>
                        {spoilage.notes && (
                          <span className="italic">"{spoilage.notes}"</span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteSpoilage(spoilage.id)}
                      disabled={deleteSpoilageMutation.isPending}
                      className="p-2 hover:bg-red-200 rounded-lg transition-colors"
                      title="Usun strate"
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
  )
}
