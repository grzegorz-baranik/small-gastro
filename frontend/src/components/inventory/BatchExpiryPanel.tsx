import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, AlertCircle, ChevronDown, ChevronRight, Package, Calendar, Clock } from 'lucide-react'
import { getExpiryAlerts, getBatchesForIngredient } from '../../api/batches'
import { formatQuantity } from '../../utils/formatters'
import type { ExpiryAlert, IngredientBatch, UnitType } from '../../types'
import LoadingSpinner from '../common/LoadingSpinner'

// Infer unit type from unit label
function inferUnitType(unitLabel: string): UnitType {
  const weightLabels = ['kg', 'g', 'gram', 'kilogram']
  return weightLabels.some(w => unitLabel.toLowerCase().includes(w)) ? 'weight' : 'count'
}

interface BatchExpiryPanelProps {
  ingredientIds?: number[]
}

export default function BatchExpiryPanel({ ingredientIds }: BatchExpiryPanelProps) {
  const { t } = useTranslation()
  const [expandedIngredients, setExpandedIngredients] = useState<Set<number>>(new Set())

  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['expiryAlerts'],
    queryFn: () => getExpiryAlerts(7),
  })

  const toggleExpanded = (ingredientId: number) => {
    setExpandedIngredients((prev) => {
      const next = new Set(prev)
      if (next.has(ingredientId)) {
        next.delete(ingredientId)
      } else {
        next.add(ingredientId)
      }
      return next
    })
  }

  if (alertsLoading) {
    return <LoadingSpinner />
  }

  const alerts = alertsData?.alerts || []
  const expiredCount = alertsData?.expired_count || 0
  const criticalCount = alertsData?.critical_count || 0
  const warningCount = alertsData?.warning_count || 0

  // Group alerts by ingredient
  const alertsByIngredient = alerts.reduce(
    (acc, alert) => {
      if (!acc[alert.ingredient_id]) {
        acc[alert.ingredient_id] = []
      }
      acc[alert.ingredient_id].push(alert)
      return acc
    },
    {} as Record<number, ExpiryAlert[]>
  )

  const ingredientIdsToShow = ingredientIds || Object.keys(alertsByIngredient).map(Number)

  return (
    <div className="space-y-4">
      {/* Expiry Alerts Summary */}
      {(expiredCount > 0 || criticalCount > 0 || warningCount > 0) && (
        <div
          className={`p-4 rounded-lg border ${
            expiredCount > 0
              ? 'bg-red-50 border-red-200'
              : criticalCount > 0
                ? 'bg-orange-50 border-orange-200'
                : 'bg-yellow-50 border-yellow-200'
          }`}
        >
          <div className="flex items-start gap-3">
            {expiredCount > 0 ? (
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <h4
                className={`font-medium ${
                  expiredCount > 0
                    ? 'text-red-800'
                    : criticalCount > 0
                      ? 'text-orange-800'
                      : 'text-yellow-800'
                }`}
              >
                {t('batch.expiryAlerts')}
              </h4>
              <div className="flex gap-4 mt-2 text-sm">
                {expiredCount > 0 && (
                  <span className="text-red-600 font-medium">
                    {expiredCount} {t('batch.expired')}
                  </span>
                )}
                {criticalCount > 0 && (
                  <span className="text-orange-600 font-medium">
                    {criticalCount} &lt;3 {t('batch.daysUntilExpiry')}
                  </span>
                )}
                {warningCount > 0 && (
                  <span className="text-yellow-600 font-medium">
                    {warningCount} &lt;7 {t('batch.daysUntilExpiry')}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Batch List by Ingredient */}
      <div className="space-y-2">
        {ingredientIdsToShow.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {t('batch.noBatches')}
          </div>
        ) : (
          ingredientIdsToShow.map((ingredientId) => (
            <IngredientBatchRow
              key={ingredientId}
              ingredientId={ingredientId}
              alerts={alertsByIngredient[ingredientId] || []}
              isExpanded={expandedIngredients.has(ingredientId)}
              onToggle={() => toggleExpanded(ingredientId)}
            />
          ))
        )}
      </div>
    </div>
  )
}

interface IngredientBatchRowProps {
  ingredientId: number
  alerts: ExpiryAlert[]
  isExpanded: boolean
  onToggle: () => void
}

function IngredientBatchRow({ ingredientId, alerts, isExpanded, onToggle }: IngredientBatchRowProps) {
  const { t } = useTranslation()

  const { data: batches, isLoading } = useQuery({
    queryKey: ['ingredientBatches', ingredientId],
    queryFn: () => getBatchesForIngredient(ingredientId),
    enabled: isExpanded,
  })

  const hasAlerts = alerts.length > 0
  const hasExpired = alerts.some((a) => a.days_until_expiry !== undefined && a.days_until_expiry < 0)
  const hasCritical = alerts.some(
    (a) => a.days_until_expiry !== undefined && a.days_until_expiry >= 0 && a.days_until_expiry < 3
  )

  // Get ingredient name from first alert or first batch
  const ingredientName = alerts[0]?.ingredient_name || batches?.[0]?.ingredient_name || `Ingredient #${ingredientId}`

  return (
    <div
      className={`border rounded-lg overflow-hidden ${
        hasExpired
          ? 'border-red-200 bg-red-50/30'
          : hasCritical
            ? 'border-orange-200 bg-orange-50/30'
            : hasAlerts
              ? 'border-yellow-200 bg-yellow-50/30'
              : 'border-gray-200'
      }`}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-50/50 transition-colors"
        aria-expanded={isExpanded}
        aria-label={`${ingredientName} batches`}
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
          <Package className="w-4 h-4 text-gray-400" />
          <span className="font-medium text-gray-900">{ingredientName}</span>
        </div>
        <div className="flex items-center gap-2">
          {hasExpired && (
            <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">
              {t('batch.expired')}
            </span>
          )}
          {hasCritical && !hasExpired && (
            <span className="px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-700 rounded">
              {t('batch.expiringSoon')}
            </span>
          )}
          {hasAlerts && !hasExpired && !hasCritical && (
            <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded">
              {t('batch.expiringSoon')}
            </span>
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-white">
          {isLoading ? (
            <div className="p-4">
              <LoadingSpinner />
            </div>
          ) : batches && batches.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {batches.map((batch, index) => (
                <BatchRow key={batch.id} batch={batch} fifoOrder={index + 1} />
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-gray-500 text-sm">
              {t('batch.noBatches')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface BatchRowProps {
  batch: IngredientBatch
  fifoOrder: number
}

function BatchRow({ batch, fifoOrder }: BatchRowProps) {
  const { t } = useTranslation()

  const daysUntilExpiry = batch.expiry_date
    ? Math.ceil((new Date(batch.expiry_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null

  const isExpired = daysUntilExpiry !== null && daysUntilExpiry < 0
  const isCritical = daysUntilExpiry !== null && daysUntilExpiry >= 0 && daysUntilExpiry < 3
  const isWarning = daysUntilExpiry !== null && daysUntilExpiry >= 3 && daysUntilExpiry < 7

  // Use pre-calculated age_days from API, or calculate from created_at as fallback
  const ageDays = batch.age_days ?? (batch.created_at
    ? Math.floor((Date.now() - new Date(batch.created_at).getTime()) / (1000 * 60 * 60 * 24))
    : null)

  return (
    <div
      className={`p-3 ${
        isExpired
          ? 'bg-red-50'
          : isCritical
            ? 'bg-orange-50'
            : isWarning
              ? 'bg-yellow-50'
              : ''
      }`}
      data-testid={`batch-row-${batch.id}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* FIFO Order Badge */}
          <span
            className="w-6 h-6 flex items-center justify-center text-xs font-medium bg-gray-100 text-gray-600 rounded-full"
            title={`FIFO #${fifoOrder}`}
            data-testid="fifo-badge"
          >
            {fifoOrder}
          </span>
          <div>
            <p className="text-sm font-medium text-gray-900" data-testid="batch-number">
              {batch.batch_number}
            </p>
            <p className="text-xs text-gray-500">
              {batch.location === 'storage' ? t('common.storage') : t('common.shop')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          {/* Quantity */}
          <div className="text-right">
            <p className="font-medium text-gray-900" data-testid="batch-quantity">
              {formatQuantity(batch.remaining_quantity, inferUnitType(batch.unit_label), batch.unit_label)}
            </p>
            <p className="text-xs text-gray-500">
              {t('common.remaining')}
            </p>
          </div>

          {/* Expiry Date */}
          {batch.expiry_date && (
            <div className="text-right min-w-[80px]">
              <div className="flex items-center justify-end gap-1">
                <Calendar className="w-3 h-3 text-gray-400" />
                <p
                  className={`font-medium ${
                    isExpired
                      ? 'text-red-600'
                      : isCritical
                        ? 'text-orange-600'
                        : isWarning
                          ? 'text-yellow-600'
                          : 'text-gray-900'
                  }`}
                  data-testid="expiry-date"
                >
                  {new Date(batch.expiry_date).toLocaleDateString('pl-PL')}
                </p>
              </div>
              <p
                className={`text-xs ${
                  isExpired
                    ? 'text-red-500'
                    : isCritical
                      ? 'text-orange-500'
                      : isWarning
                        ? 'text-yellow-500'
                        : 'text-gray-500'
                }`}
                data-testid="days-until-expiry"
              >
                {isExpired
                  ? t('batch.expired')
                  : `${daysUntilExpiry} ${t('batch.daysUntilExpiry')}`}
              </p>
            </div>
          )}

          {/* Age */}
          {ageDays !== null && (
            <div className="text-right min-w-[60px]">
              <div className="flex items-center justify-end gap-1">
                <Clock className="w-3 h-3 text-gray-400" />
                <p className="text-gray-600" data-testid="batch-age">
                  {ageDays}d
                </p>
              </div>
              <p className="text-xs text-gray-500">{t('common.age')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Notes */}
      {batch.notes && (
        <p className="mt-2 text-xs text-gray-500 italic">{batch.notes}</p>
      )}
    </div>
  )
}
