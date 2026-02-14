import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Trash2, ShoppingCart } from 'lucide-react'
import { getSalesForDay, createSale, deleteSale } from '../../../api/sales'
import { getProducts } from '../../../api/products'
import { formatCurrency } from '../../../utils/formatters'
import LoadingSpinner from '../../common/LoadingSpinner'

interface DaySalesSectionProps {
  dayId: number
  isEditable: boolean
}

export default function DaySalesSection({ dayId, isEditable }: DaySalesSectionProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  // Fetch sales for this day
  const { data: salesData, isLoading: salesLoading } = useQuery({
    queryKey: ['daySales', dayId],
    queryFn: () => getSalesForDay(dayId),
    enabled: !!dayId,
  })

  // Fetch products for quick add buttons
  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: () => getProducts(true),
    enabled: isEditable,
  })

  // Create sale mutation
  const createSaleMutation = useMutation({
    mutationFn: createSale,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daySales', dayId] })
      queryClient.invalidateQueries({ queryKey: ['daySummary', dayId] })
    },
  })

  // Delete sale mutation
  const deleteSaleMutation = useMutation({
    mutationFn: deleteSale,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daySales', dayId] })
      queryClient.invalidateQueries({ queryKey: ['daySummary', dayId] })
    },
  })

  // Handle quick sale - adds 1 unit of a product
  const handleQuickSale = (productId: number) => {
    createSaleMutation.mutate({
      product_id: productId,
      quantity_sold: 1,
    })
  }

  return (
    <div className="space-y-6">
      {/* Quick sales entry - only show if editable */}
      {isEditable && productsData && productsData.items.length > 0 && (
        <div className="card">
          <h3 className="card-header">{t('dailyOperations.addSale')}</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {productsData.items.map((product) => (
              <button
                key={product.id}
                onClick={() => handleQuickSale(product.id)}
                disabled={createSaleMutation.isPending}
                className="p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <p className="font-medium text-gray-900">{product.name}</p>
                <p className="text-primary-600 font-bold">
                  {formatCurrency(product.variants[0]?.price_pln ?? 0)}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Sales list */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="card-header mb-0">
            {isEditable ? t('dailyOperations.todaySales') : t('inventory.soldProducts')}
          </h3>
          <div className="text-right">
            <p className="text-sm text-gray-500">{t('common.sum')}</p>
            <p className="text-xl font-bold text-primary-600">
              {formatCurrency(salesData?.total_revenue ?? 0)}
            </p>
          </div>
        </div>

        {salesLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : !salesData?.items || salesData.items.length === 0 ? (
          <div className="empty-state py-8">
            <ShoppingCart className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-center">{t('dailyOperations.noSales')}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {salesData.items.map((sale) => (
              <div
                key={sale.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">{sale.product_name}</p>
                  <p className="text-sm text-gray-500">
                    {sale.quantity_sold} x {formatCurrency(sale.unit_price)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <p className="font-bold text-gray-900">
                    {formatCurrency(sale.total_price)}
                  </p>
                  {isEditable && (
                    <button
                      onClick={() => deleteSaleMutation.mutate(sale.id)}
                      disabled={deleteSaleMutation.isPending}
                      className="p-2 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50"
                      title={t('common.delete')}
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Total items sold */}
        {salesData && salesData.items.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between items-center text-sm">
            <span className="text-gray-500">
              {t('common.total')}: {salesData.total_items_sold} {t('common.items')}
            </span>
            <span className="font-semibold text-gray-900">
              {formatCurrency(salesData.total_revenue)}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
