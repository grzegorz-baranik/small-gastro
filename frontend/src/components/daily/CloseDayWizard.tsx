import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Loader2, ChevronLeft, ChevronRight, XCircle } from 'lucide-react'
import Modal from '../common/Modal'
import WizardStepper, { type WizardStep } from '../common/WizardStepper'
import WizardStepOpening from './wizard/WizardStepOpening'
import WizardStepEvents from './wizard/WizardStepEvents'
import WizardStepClosing from './wizard/WizardStepClosing'
import WizardStepReconciliation from './wizard/WizardStepReconciliation'
import WizardStepConfirm from './wizard/WizardStepConfirm'
import { useClosingCalculations } from '../../hooks/useClosingCalculations'
import {
  getDaySummary,
  closeDay,
  getPreviousClosing,
  getReconciliationReport,
} from '../../api/dailyOperations'
import {
  getDeliveries,
  getTransfers,
  getSpoilage,
} from '../../api/midDayOperations'
import { formatDate } from '../../utils/formatters'
import type { DailyRecord, DeliverySummaryItem, TransferSummaryItem, SpoilageSummaryItem } from '../../types'

interface CloseDayWizardProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  dailyRecord: DailyRecord
}

export default function CloseDayWizard({
  isOpen,
  onClose,
  onSuccess,
  dailyRecord,
}: CloseDayWizardProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [currentStep, setCurrentStep] = useState(0)
  const [closingInventory, setClosingInventory] = useState<
    Record<number, string>
  >({})
  const [notes, setNotes] = useState('')
  const [reconciliationNotes, setReconciliationNotes] = useState('')

  // Fetch day summary
  const {
    data: daySummary,
    isLoading: isSummaryLoading,
  } = useQuery({
    queryKey: ['daySummary', dailyRecord.id],
    queryFn: () => getDaySummary(dailyRecord.id),
    enabled: isOpen,
    staleTime: 30000, // 30 seconds
  })

  // Fetch previous closing for comparison
  const { data: previousClosingData } = useQuery({
    queryKey: ['previousClosing'],
    queryFn: getPreviousClosing,
    enabled: isOpen,
    staleTime: 60000,
  })

  // Fetch deliveries
  const { data: deliveries = [] } = useQuery({
    queryKey: ['deliveries', dailyRecord.id],
    queryFn: () => getDeliveries(dailyRecord.id),
    enabled: isOpen,
    staleTime: 30000,
  })

  // Fetch transfers
  const { data: transfers = [] } = useQuery({
    queryKey: ['transfers', dailyRecord.id],
    queryFn: () => getTransfers(dailyRecord.id),
    enabled: isOpen,
    staleTime: 30000,
  })

  // Fetch spoilage
  const { data: spoilage = [] } = useQuery({
    queryKey: ['spoilage', dailyRecord.id],
    queryFn: () => getSpoilage(dailyRecord.id),
    enabled: isOpen,
    staleTime: 30000,
  })

  // Fetch reconciliation report (for step 4)
  const {
    data: reconciliationReport,
    isLoading: isReconciliationLoading,
    isError: isReconciliationError,
  } = useQuery({
    queryKey: ['reconciliation', dailyRecord.id],
    queryFn: () => getReconciliationReport(dailyRecord.id),
    enabled: isOpen && currentStep >= 3, // Only fetch when reaching reconciliation step
    staleTime: 30000,
  })

  // Flatten deliveries for the wizard (deliveries have nested items)
  const flattenedDeliveries: DeliverySummaryItem[] = useMemo(() => {
    return deliveries.flatMap((delivery) =>
      delivery.items.map((item) => ({
        id: item.id,
        ingredient_id: item.ingredient_id,
        ingredient_name: item.ingredient_name,
        unit_label: item.unit_label,
        quantity: item.quantity,
        price_pln: item.cost_pln ?? delivery.total_cost_pln / delivery.items.length,
        delivered_at: delivery.delivered_at,
      }))
    )
  }, [deliveries])

  // Convert transfers and spoilage to summary types
  const transferSummaries: TransferSummaryItem[] = useMemo(() => {
    return transfers.map((t) => ({
      id: t.id,
      ingredient_id: t.ingredient_id,
      ingredient_name: t.ingredient_name,
      unit_label: t.unit_label,
      quantity: t.quantity,
      transferred_at: t.transferred_at,
    }))
  }, [transfers])

  const spoilageSummaries: SpoilageSummaryItem[] = useMemo(() => {
    return spoilage.map((s) => ({
      id: s.id,
      ingredient_id: s.ingredient_id,
      ingredient_name: s.ingredient_name,
      unit_label: s.unit_label,
      quantity: s.quantity,
      reason: s.reason,
      notes: s.notes,
      recorded_at: s.recorded_at,
    }))
  }, [spoilage])

  // Real-time calculations
  const { rows, alerts, isValid } = useClosingCalculations({
    usageItems: daySummary?.usage_items || [],
    closingInventory,
  })

  // Close mutation
  const closeMutation = useMutation({
    mutationFn: () =>
      closeDay(
        dailyRecord.id,
        rows.map((r) => ({
          ingredient_id: r.ingredientId,
          quantity: r.closing!,
        })),
        notes || undefined
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daySummary'] })
      queryClient.invalidateQueries({ queryKey: ['dailyRecord'] })
      queryClient.invalidateQueries({ queryKey: ['openRecord'] })
      queryClient.invalidateQueries({ queryKey: ['todayRecord'] })
      onSuccess()
      onClose()
    },
  })

  // Define wizard steps (5 steps now: Opening, Events, Closing, Reconciliation, Confirm)
  const steps: WizardStep[] = useMemo(
    () => [
      {
        id: 1,
        title: t('wizard.step1Title'),
        status:
          currentStep > 0
            ? 'completed'
            : currentStep === 0
              ? 'current'
              : 'pending',
      },
      {
        id: 2,
        title: t('wizard.step2Title'),
        status:
          currentStep > 1
            ? 'completed'
            : currentStep === 1
              ? 'current'
              : 'pending',
      },
      {
        id: 3,
        title: t('wizard.step3Title'),
        status:
          currentStep > 2
            ? 'completed'
            : currentStep === 2
              ? 'current'
              : 'pending',
      },
      {
        id: 4,
        title: t('wizard.step5Title'),
        status:
          currentStep > 3
            ? 'completed'
            : currentStep === 3
              ? 'current'
              : 'pending',
      },
      {
        id: 5,
        title: t('wizard.step4Title'),
        status:
          currentStep > 4
            ? 'completed'
            : currentStep === 4
              ? 'current'
              : 'pending',
      },
    ],
    [currentStep, t]
  )

  // Total number of steps (0-indexed, so last step is 4)
  const totalSteps = 5

  // Step navigation
  const canProceed = useMemo(() => {
    if (currentStep === 2) {
      // Step 3 requires valid inputs (all closing quantities filled)
      return isValid
    }
    // Step 4 (Reconciliation) never blocks - it's informational only
    return true
  }, [currentStep, isValid])

  const handleNext = () => {
    if (canProceed && currentStep < totalSteps - 1) {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  const handleStepClick = (stepIndex: number) => {
    // Only allow going back to completed steps
    if (stepIndex < currentStep) {
      setCurrentStep(stepIndex)
    }
  }

  const handleClose = () => {
    closeMutation.mutate()
  }

  const handleCancel = () => {
    // Reset state when modal closes
    setCurrentStep(0)
    setClosingInventory({})
    setNotes('')
    setReconciliationNotes('')
    onClose()
  }

  const isLoading = isSummaryLoading

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCancel}
      title={t('closeDayModal.title', { date: formatDate(dailyRecord.date) })}
      size="3xl"
      preventClose={closeMutation.isPending}
      data-testid="close-day-wizard"
    >
      <div className="flex flex-col" style={{ minHeight: '500px' }}>
        {/* Stepper */}
        <div className="mb-6 pt-2 pb-4 border-b border-gray-100">
          <WizardStepper
            steps={steps}
            currentStep={currentStep}
            onStepClick={handleStepClick}
          />
        </div>

        {/* Step content */}
        <div className="flex-1 overflow-y-auto mb-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
          ) : (
            <>
              {currentStep === 0 && (
                <WizardStepOpening
                  daySummary={daySummary}
                  previousClosing={previousClosingData?.items}
                />
              )}
              {currentStep === 1 && (
                <WizardStepEvents
                  daySummary={daySummary}
                  deliveries={flattenedDeliveries}
                  transfers={transferSummaries}
                  spoilage={spoilageSummaries}
                />
              )}
              {currentStep === 2 && (
                <WizardStepClosing
                  rows={rows}
                  closingInventory={closingInventory}
                  onChange={setClosingInventory}
                  alerts={alerts}
                />
              )}
              {currentStep === 3 && (
                <WizardStepReconciliation
                  report={reconciliationReport}
                  isLoading={isReconciliationLoading}
                  isError={isReconciliationError}
                  notes={reconciliationNotes}
                  onNotesChange={setReconciliationNotes}
                />
              )}
              {currentStep === 4 && (
                <WizardStepConfirm
                  daySummary={daySummary}
                  rows={rows}
                  alerts={alerts}
                  notes={notes}
                  onNotesChange={setNotes}
                />
              )}
            </>
          )}
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={handleCancel}
            disabled={closeMutation.isPending}
            data-testid="wizard-cancel-btn"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <XCircle className="w-4 h-4" />
            {t('common.cancel')}
          </button>

          <div className="flex gap-3">
            {currentStep > 0 && (
              <button
                type="button"
                onClick={handleBack}
                disabled={closeMutation.isPending}
                data-testid="wizard-back-btn"
                className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
                {t('wizard.back')}
              </button>
            )}

            {currentStep < totalSteps - 1 ? (
              <button
                type="button"
                onClick={handleNext}
                disabled={!canProceed || isLoading}
                data-testid="wizard-next-btn"
                className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {t('wizard.next')}
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleClose}
                disabled={closeMutation.isPending || !isValid}
                data-testid="wizard-close-day-btn"
                className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {closeMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {t('common.saving')}
                  </>
                ) : (
                  <>
                    {t('dailyOperations.closeDay')}
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Error message */}
        {closeMutation.isError && (
          <div data-testid="wizard-error-message" className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {t('errors.closeDayFailed')}
          </div>
        )}
      </div>
    </Modal>
  )
}
