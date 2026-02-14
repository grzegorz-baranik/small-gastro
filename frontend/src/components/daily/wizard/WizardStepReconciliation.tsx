import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import {
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Info,
  FileText,
  TrendingUp,
  TrendingDown,
  Equal,
  HelpCircle,
  Loader2,
} from 'lucide-react'
import { formatCurrency } from '../../../utils/formatters'
import type {
  ReconciliationReport,
  ProductReconciliation,
  MissingSuggestion,
} from '../../../types'

interface WizardStepReconciliationProps {
  report: ReconciliationReport | undefined
  isLoading: boolean
  isError: boolean
  notes: string
  onNotesChange: (notes: string) => void
}

// Status types based on discrepancy levels
type ReconciliationStatus = 'ideal' | 'acceptable' | 'review_recommended' | 'investigation_needed'
type ProductStatus = 'match' | 'minor_discrepancy' | 'major_discrepancy' | 'recorded_only' | 'calculated_only'

export default function WizardStepReconciliation({
  report,
  isLoading,
  isError,
  notes,
  onNotesChange,
}: WizardStepReconciliationProps) {
  const { t } = useTranslation()

  // Determine overall status based on discrepancy percentage
  const overallStatus = useMemo((): ReconciliationStatus => {
    if (!report) return 'ideal'
    if (report.has_critical_discrepancy) return 'investigation_needed'
    const percent = Math.abs(report.discrepancy_percent)
    if (percent <= 1) return 'ideal'
    if (percent <= 5) return 'acceptable'
    if (percent <= 10) return 'review_recommended'
    return 'investigation_needed'
  }, [report])

  // Determine product status based on qty/revenue difference
  const getProductStatus = (product: ProductReconciliation): ProductStatus => {
    // Check if only one side has data
    if (product.recorded_qty === 0 && product.calculated_qty > 0) return 'calculated_only'
    if (product.calculated_qty === 0 && product.recorded_qty > 0) return 'recorded_only'

    // Check discrepancy level
    const qtyDiffPercent = product.recorded_qty > 0
      ? Math.abs(product.qty_difference / product.recorded_qty) * 100
      : 0

    if (qtyDiffPercent <= 1) return 'match'
    if (qtyDiffPercent <= 10) return 'minor_discrepancy'
    return 'major_discrepancy'
  }

  // Separate products by status
  const { matchingProducts, discrepancyProducts, recordedOnlyProducts, calculatedOnlyProducts } =
    useMemo(() => {
      if (!report) {
        return {
          matchingProducts: [],
          discrepancyProducts: [],
          recordedOnlyProducts: [],
          calculatedOnlyProducts: [],
        }
      }

      const matching: ProductReconciliation[] = []
      const discrepancy: ProductReconciliation[] = []
      const recordedOnly: ProductReconciliation[] = []
      const calculatedOnly: ProductReconciliation[] = []

      report.by_product.forEach((product) => {
        const status = getProductStatus(product)
        switch (status) {
          case 'match':
            matching.push(product)
            break
          case 'minor_discrepancy':
          case 'major_discrepancy':
            discrepancy.push(product)
            break
          case 'recorded_only':
            recordedOnly.push(product)
            break
          case 'calculated_only':
            calculatedOnly.push(product)
            break
        }
      })

      return {
        matchingProducts: matching,
        discrepancyProducts: discrepancy,
        recordedOnlyProducts: recordedOnly,
        calculatedOnlyProducts: calculatedOnly,
      }
    }, [report])

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600 mb-3" />
        <p className="text-sm text-gray-500">{t('reconciliation.loading')}</p>
      </div>
    )
  }

  if (isError || !report) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
        <p className="text-sm text-red-600">{t('reconciliation.error')}</p>
      </div>
    )
  }

  const hasAnyDiscrepancy =
    discrepancyProducts.length > 0 ||
    recordedOnlyProducts.length > 0 ||
    calculatedOnlyProducts.length > 0

  return (
    <div className="space-y-6">
      {/* Header Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-xs text-blue-600 uppercase font-medium">
            {t('reconciliation.recordedSales')}
          </div>
          <div className="text-xl font-bold text-blue-800 mt-1">
            {formatCurrency(report.recorded_total_pln)}
          </div>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <div className="text-xs text-purple-600 uppercase font-medium">
            {t('reconciliation.calculatedSales')}
          </div>
          <div className="text-xl font-bold text-purple-800 mt-1">
            {formatCurrency(report.calculated_total_pln)}
          </div>
        </div>
        <div
          className={`p-4 rounded-lg border ${getDiscrepancyCardStyle(report.discrepancy_pln)}`}
        >
          <div className="text-xs uppercase font-medium">
            {t('reconciliation.discrepancy')}
          </div>
          <div className="text-xl font-bold mt-1 flex items-center gap-2">
            {report.discrepancy_pln > 0 ? (
              <TrendingUp className="w-5 h-5" />
            ) : report.discrepancy_pln < 0 ? (
              <TrendingDown className="w-5 h-5" />
            ) : (
              <Equal className="w-5 h-5" />
            )}
            {formatCurrency(Math.abs(report.discrepancy_pln))}
            <span className="text-sm font-normal">
              ({report.discrepancy_percent > 0 ? '+' : ''}
              {report.discrepancy_percent.toFixed(1)}%)
            </span>
          </div>
        </div>
      </div>

      {/* Overall Status Indicator */}
      <div className={`p-4 rounded-lg border ${getStatusAlertStyle(overallStatus)}`}>
        <div className="flex items-start gap-3">
          {getStatusIcon(overallStatus)}
          <div>
            <h4 className="font-medium">{t(`reconciliation.status.${overallStatus}`)}</h4>
            {!hasAnyDiscrepancy ? (
              <p className="text-sm mt-1">{t('reconciliation.allMatches')}</p>
            ) : (
              <p className="text-sm mt-1">{t('reconciliation.infoText')}</p>
            )}
          </div>
        </div>
      </div>

      {/* Products Table - Only show if there are products with discrepancies */}
      {(discrepancyProducts.length > 0 || matchingProducts.length > 0) && (
        <div>
          <h3 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
            <FileText className="w-4 h-4" />
            {t('reconciliation.productsComparison')}
          </h3>
          <div className="border border-gray-200 rounded-lg overflow-hidden overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    {t('reconciliation.product')}
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-blue-600 uppercase">
                    {t('reconciliation.recordedQty')}
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-purple-600 uppercase">
                    {t('reconciliation.calculatedQty')}
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                    {t('reconciliation.qtyDiscrepancy')}
                  </th>
                  <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                    {t('common.status')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {/* Show discrepancy products first */}
                {discrepancyProducts.map((product) => (
                  <ProductRow key={getProductKey(product)} product={product} t={t} getProductStatus={getProductStatus} />
                ))}
                {/* Then matching products */}
                {matchingProducts.map((product) => (
                  <ProductRow key={getProductKey(product)} product={product} t={t} getProductStatus={getProductStatus} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recorded Only Section */}
      {recordedOnlyProducts.length > 0 && (
        <div>
          <h3 className="flex items-center gap-2 text-sm font-medium text-yellow-700 mb-3">
            <AlertTriangle className="w-4 h-4" />
            {t('reconciliation.recordedOnlySection')}
          </h3>
          <p className="text-xs text-gray-500 mb-2">{t('reconciliation.recordedOnlyHint')}</p>
          <div className="border border-yellow-200 rounded-lg overflow-hidden bg-yellow-50/50">
            <table className="w-full text-sm">
              <thead className="bg-yellow-100/50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-yellow-700 uppercase">
                    {t('reconciliation.product')}
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-yellow-700 uppercase">
                    {t('reconciliation.recordedQty')}
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-yellow-700 uppercase">
                    {t('wizard.revenue')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-yellow-200">
                {recordedOnlyProducts.map((product) => (
                  <tr key={getProductKey(product)}>
                    <td className="px-3 py-2">
                      <span className="font-medium text-gray-900">{product.product_name}</span>
                      {product.variant_name && (
                        <span className="text-xs text-gray-500 ml-1">
                          ({product.variant_name})
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-900">
                      {product.recorded_qty}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-900">
                      {formatCurrency(product.recorded_revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Calculated Only Section */}
      {calculatedOnlyProducts.length > 0 && (
        <div>
          <h3 className="flex items-center gap-2 text-sm font-medium text-orange-700 mb-3">
            <HelpCircle className="w-4 h-4" />
            {t('reconciliation.calculatedOnlySection')}
          </h3>
          <p className="text-xs text-gray-500 mb-2">{t('reconciliation.calculatedOnlyHint')}</p>
          <div className="border border-orange-200 rounded-lg overflow-hidden bg-orange-50/50">
            <table className="w-full text-sm">
              <thead className="bg-orange-100/50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-orange-700 uppercase">
                    {t('reconciliation.product')}
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-orange-700 uppercase">
                    {t('reconciliation.calculatedQty')}
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-orange-700 uppercase">
                    {t('wizard.revenue')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-orange-200">
                {calculatedOnlyProducts.map((product) => (
                  <tr key={getProductKey(product)}>
                    <td className="px-3 py-2">
                      <span className="font-medium text-gray-900">{product.product_name}</span>
                      {product.variant_name && (
                        <span className="text-xs text-gray-500 ml-1">
                          ({product.variant_name})
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-900">
                      {product.calculated_qty}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-900">
                      {formatCurrency(product.calculated_revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Suggestions Section */}
      {report.suggestions.length > 0 && (
        <div>
          <h3 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
            <Info className="w-4 h-4" />
            {t('reconciliation.suggestions')}
          </h3>
          <div className="space-y-2">
            {report.suggestions.map((suggestion, index) => (
              <SuggestionCard key={index} suggestion={suggestion} />
            ))}
          </div>
        </div>
      )}

      {/* Notes Section */}
      <div>
        <h3 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
          <FileText className="w-4 h-4" />
          {t('reconciliation.notesLabel')}{' '}
          <span className="text-gray-400 font-normal">({t('common.optional')})</span>
        </h3>
        <textarea
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          placeholder={t('reconciliation.notesPlaceholder')}
        />
      </div>

      {/* Info Box */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-800">{t('reconciliation.infoTitle')}</h4>
            <p className="text-sm text-blue-600 mt-1">{t('reconciliation.infoText')}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper Components
function ProductRow({
  product,
  t,
  getProductStatus,
}: {
  product: ProductReconciliation
  t: (key: string) => string
  getProductStatus: (product: ProductReconciliation) => ProductStatus
}) {
  const status = getProductStatus(product)
  const rowClass = getRowClass(status)
  const statusBadge = getStatusBadge(status, product, t)

  return (
    <tr className={rowClass}>
      <td className="px-3 py-2">
        <span className="font-medium text-gray-900">{product.product_name}</span>
        {product.variant_name && (
          <span className="text-xs text-gray-500 ml-1">({product.variant_name})</span>
        )}
      </td>
      <td className="px-3 py-2 text-right text-blue-600">{product.recorded_qty}</td>
      <td className="px-3 py-2 text-right text-purple-600">{product.calculated_qty}</td>
      <td className="px-3 py-2 text-right">
        <span
          className={
            product.qty_difference > 0
              ? 'text-green-600'
              : product.qty_difference < 0
                ? 'text-red-600'
                : 'text-gray-500'
          }
        >
          {product.qty_difference > 0 ? '+' : ''}
          {product.qty_difference}
        </span>
      </td>
      <td className="px-3 py-2 text-center">{statusBadge}</td>
    </tr>
  )
}

function SuggestionCard({ suggestion }: { suggestion: MissingSuggestion }) {
  return (
    <div className="p-3 rounded-lg border bg-gray-50 border-gray-200">
      <div className="flex items-start gap-2">
        <HelpCircle className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-900">
            {suggestion.product_name}
            {suggestion.variant_name && (
              <span className="text-gray-500 font-normal"> ({suggestion.variant_name})</span>
            )}
          </div>
          <p className="text-xs text-gray-600 mt-1">{suggestion.reason}</p>
        </div>
      </div>
    </div>
  )
}

// Helper Functions
function getProductKey(product: ProductReconciliation): string {
  return `${product.product_variant_id}`
}

function getDiscrepancyCardStyle(discrepancy: number): string {
  if (Math.abs(discrepancy) < 0.01) {
    return 'bg-green-50 border-green-200 text-green-800'
  }
  if (Math.abs(discrepancy) <= 50) {
    return 'bg-yellow-50 border-yellow-200 text-yellow-800'
  }
  return 'bg-red-50 border-red-200 text-red-800'
}

function getStatusAlertStyle(status: ReconciliationStatus): string {
  switch (status) {
    case 'ideal':
      return 'bg-green-50 border-green-200'
    case 'acceptable':
      return 'bg-blue-50 border-blue-200'
    case 'review_recommended':
      return 'bg-yellow-50 border-yellow-200'
    case 'investigation_needed':
      return 'bg-red-50 border-red-200'
  }
}

function getStatusIcon(status: ReconciliationStatus): JSX.Element {
  switch (status) {
    case 'ideal':
      return <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
    case 'acceptable':
      return <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
    case 'review_recommended':
      return <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
    case 'investigation_needed':
      return <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
  }
}

function getRowClass(status: ProductStatus): string {
  switch (status) {
    case 'match':
      return ''
    case 'minor_discrepancy':
      return 'bg-yellow-50/30'
    case 'major_discrepancy':
      return 'bg-red-50/30'
    case 'recorded_only':
      return 'bg-yellow-50/50'
    case 'calculated_only':
      return 'bg-orange-50/50'
  }
}

function getStatusBadge(
  status: ProductStatus,
  product: ProductReconciliation,
  t: (key: string) => string
): JSX.Element {
  // Calculate discrepancy percentage for display
  const discrepancyPercent = product.recorded_qty > 0
    ? (product.qty_difference / product.recorded_qty) * 100
    : null

  const configs: Record<
    ProductStatus,
    { bg: string; icon: JSX.Element; label: string }
  > = {
    match: {
      bg: 'bg-green-100 text-green-800 border-green-200',
      icon: <CheckCircle className="w-3.5 h-3.5" />,
      label: t('reconciliation.productStatus.match'),
    },
    minor_discrepancy: {
      bg: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
      label:
        discrepancyPercent !== null ? `${discrepancyPercent.toFixed(0)}%` : t('reconciliation.productStatus.minor_discrepancy'),
    },
    major_discrepancy: {
      bg: 'bg-red-100 text-red-800 border-red-200',
      icon: <AlertCircle className="w-3.5 h-3.5" />,
      label:
        discrepancyPercent !== null ? `${discrepancyPercent.toFixed(0)}%` : t('reconciliation.productStatus.major_discrepancy'),
    },
    recorded_only: {
      bg: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
      label: t('reconciliation.productStatus.recorded_only'),
    },
    calculated_only: {
      bg: 'bg-orange-100 text-orange-800 border-orange-200',
      icon: <HelpCircle className="w-3.5 h-3.5" />,
      label: t('reconciliation.productStatus.calculated_only'),
    },
  }

  const { bg, icon, label } = configs[status]

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${bg}`}>
      {icon}
      <span>{label}</span>
    </div>
  )
}
