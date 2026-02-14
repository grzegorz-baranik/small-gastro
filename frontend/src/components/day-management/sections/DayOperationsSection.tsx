import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Truck, Package, Trash2 } from 'lucide-react'
import { getDayEvents } from '../../../api/dailyOperations'
import { MidDayEventsList } from '../../daily'
import DeliveryModal from '../../daily/DeliveryModal'
import TransferModal from '../../daily/TransferModal'
import SpoilageModal from '../../daily/SpoilageModal'
import { formatCurrency } from '../../../utils/formatters'

interface DayOperationsSectionProps {
  dayId: number
  isEditable: boolean
}

export default function DayOperationsSection({
  dayId,
  isEditable,
}: DayOperationsSectionProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  // Modal states
  const [deliveryModalOpen, setDeliveryModalOpen] = useState(false)
  const [transferModalOpen, setTransferModalOpen] = useState(false)
  const [spoilageModalOpen, setSpoilageModalOpen] = useState(false)

  // Fetch day events summary
  const { data: dayEvents } = useQuery({
    queryKey: ['dayEvents', dayId],
    queryFn: () => getDayEvents(dayId),
    enabled: !!dayId,
  })

  // Handle success callback for mid-day operations
  const handleOperationSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['dayEvents', dayId] })
    queryClient.invalidateQueries({ queryKey: ['deliveries', dayId] })
    queryClient.invalidateQueries({ queryKey: ['transfers', dayId] })
    queryClient.invalidateQueries({ queryKey: ['spoilage', dayId] })
    queryClient.invalidateQueries({ queryKey: ['daySummary', dayId] })
  }

  return (
    <div className="space-y-6">
      {/* Action buttons - only show if editable */}
      {isEditable && (
        <div className="card">
          <h3 className="card-header">{t('dailyOperations.storageOperations')}</h3>
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => setDeliveryModalOpen(true)}
              className="p-4 rounded-lg border-2 border-green-200 bg-green-50 text-green-700 hover:bg-green-100 hover:border-green-300 transition-colors flex flex-col items-center gap-2"
            >
              <Truck className="w-8 h-8" />
              <span className="font-medium">{t('dailyOperations.addDelivery')}</span>
            </button>
            <button
              onClick={() => setTransferModalOpen(true)}
              className="p-4 rounded-lg border-2 border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300 transition-colors flex flex-col items-center gap-2"
            >
              <Package className="w-8 h-8" />
              <span className="font-medium">{t('dailyOperations.transferFromStorage')}</span>
            </button>
            <button
              onClick={() => setSpoilageModalOpen(true)}
              className="p-4 rounded-lg border-2 border-red-200 bg-red-50 text-red-700 hover:bg-red-100 hover:border-red-300 transition-colors flex flex-col items-center gap-2"
            >
              <Trash2 className="w-8 h-8" />
              <span className="font-medium">{t('dailyOperations.recordSpoilage')}</span>
            </button>
          </div>
        </div>
      )}

      {/* Events summary */}
      {dayEvents && (
        <div className="card">
          <h3 className="card-header">{t('dailyOperations.eventSummary')}</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <Truck className="w-6 h-6 text-green-600" />
              <div>
                <p className="text-sm text-green-600">{t('dailyOperations.deliveries')}</p>
                <p className="font-semibold text-green-800">
                  {dayEvents.deliveries_count} {t('common.items')}
                </p>
                <p className="text-sm text-green-600">
                  {formatCurrency(dayEvents.deliveries_total_pln)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
              <Package className="w-6 h-6 text-blue-600" />
              <div>
                <p className="text-sm text-blue-600">{t('dailyOperations.transfers')}</p>
                <p className="font-semibold text-blue-800">
                  {dayEvents.transfers_count} {t('common.items')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg">
              <Trash2 className="w-6 h-6 text-red-600" />
              <div>
                <p className="text-sm text-red-600">{t('dailyOperations.spoilage')}</p>
                <p className="font-semibold text-red-800">
                  {dayEvents.spoilage_count} {t('common.items')}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Events list */}
      <MidDayEventsList dailyRecordId={dayId} />

      {/* Modals - only render if editable */}
      {isEditable && (
        <>
          <DeliveryModal
            isOpen={deliveryModalOpen}
            onClose={() => setDeliveryModalOpen(false)}
            onSuccess={handleOperationSuccess}
            dailyRecordId={dayId}
          />
          <TransferModal
            isOpen={transferModalOpen}
            onClose={() => setTransferModalOpen(false)}
            onSuccess={handleOperationSuccess}
            dailyRecordId={dayId}
          />
          <SpoilageModal
            isOpen={spoilageModalOpen}
            onClose={() => setSpoilageModalOpen(false)}
            onSuccess={handleOperationSuccess}
            dailyRecordId={dayId}
          />
        </>
      )}
    </div>
  )
}
