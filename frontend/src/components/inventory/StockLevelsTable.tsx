import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, AlertTriangle, ArrowRightLeft, Edit3 } from 'lucide-react'
import { formatQuantity } from '../../utils/formatters'
import type { StockLevel } from '../../types'

interface StockLevelsTableProps {
  stockLevels: StockLevel[]
  isLoading: boolean
  onAdjust: (ingredientId: number, location: 'storage' | 'shop') => void
  onTransfer: (ingredientId: number) => void
}

export default function StockLevelsTable({
  stockLevels,
  isLoading,
  onAdjust,
  onTransfer,
}: StockLevelsTableProps) {
  const { t } = useTranslation()
  const [searchQuery, setSearchQuery] = useState('')

  // Filter stock levels based on search query
  const filteredStockLevels = useMemo(() => {
    if (!searchQuery.trim()) {
      return stockLevels
    }
    const query = searchQuery.toLowerCase()
    return stockLevels.filter((item) =>
      item.ingredient_name.toLowerCase().includes(query)
    )
  }, [stockLevels, searchQuery])

  // Check if expiry date is within 7 days
  const isExpiringSoon = (expiryDate: string | null): boolean => {
    if (!expiryDate) return false
    const daysUntilExpiry = Math.ceil(
      (new Date(expiryDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    )
    return daysUntilExpiry <= 7
  }

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-10 bg-gray-200 rounded" />
        <div className="h-12 bg-gray-100 rounded" />
        <div className="h-12 bg-gray-100 rounded" />
        <div className="h-12 bg-gray-100 rounded" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('inventory.table.search')}
          className="input w-full pl-10"
        />
      </div>

      {/* Table */}
      {filteredStockLevels.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {searchQuery ? t('common.noData') : t('inventory.table.noData')}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  {t('inventory.table.ingredient')}
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">
                  {t('inventory.table.warehouse')}
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">
                  {t('inventory.table.shop')}
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">
                  {t('inventory.table.total')}
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">
                  {t('inventory.table.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredStockLevels.map((item) => {
                const expiringSoon = isExpiringSoon(item.nearest_expiry)
                return (
                  <tr
                    key={item.ingredient_id}
                    className={`hover:bg-gray-50 transition-colors ${
                      expiringSoon ? 'bg-yellow-50/50' : ''
                    }`}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {item.ingredient_name}
                        </span>
                        {expiringSoon && (
                          <span title={t('inventory.expiry.warning')}>
                            <AlertTriangle className="w-4 h-4 text-yellow-500" />
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {item.batches_count > 0 &&
                          `${item.batches_count} ${t('inventory.expiry.batches')}`}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-gray-900">
                        {formatQuantity(item.warehouse_qty, item.unit_type, item.unit_label)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-gray-900">
                        {formatQuantity(item.shop_qty, item.unit_type, item.unit_label)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="font-medium text-gray-900">
                        {formatQuantity(item.total_qty, item.unit_type, item.unit_label)}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onAdjust(item.ingredient_id, 'storage')}
                          className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title={t('inventory.actions.adjust')}
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => onTransfer(item.ingredient_id)}
                          className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title={t('inventory.actions.transfer')}
                        >
                          <ArrowRightLeft className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
