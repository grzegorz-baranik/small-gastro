import { formatCurrency } from '../../utils/formatters'
import type { CalculatedSaleItem } from '../../types'

interface CalculatedSalesTableProps {
  sales: CalculatedSaleItem[]
  totalIncome: number
}

export default function CalculatedSalesTable({
  sales,
  totalIncome,
}: CalculatedSalesTableProps) {
  if (sales.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 border border-gray-200 rounded-lg">
        Brak sprzedazy
      </div>
    )
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
              Produkt
            </th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
              Ilosc
            </th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
              Cena
            </th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
              Przychod
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {sales.map((sale, index) => (
            <tr key={`${sale.product_id}-${sale.variant_id ?? 'default'}-${index}`}>
              <td className="px-4 py-2 font-medium text-gray-900">
                {sale.product_name}
                {sale.variant_name && (
                  <span className="text-gray-500"> ({sale.variant_name})</span>
                )}
              </td>
              <td className="px-4 py-2 text-right text-gray-900">
                {sale.quantity_sold}
              </td>
              <td className="px-4 py-2 text-right text-gray-600">
                {formatCurrency(sale.unit_price_pln)}
              </td>
              <td className="px-4 py-2 text-right font-medium text-gray-900">
                {formatCurrency(sale.revenue_pln)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-gray-50">
          <tr>
            <td
              colSpan={3}
              className="px-4 py-3 text-right font-medium text-gray-900"
            >
              RAZEM:
            </td>
            <td className="px-4 py-3 text-right font-bold text-primary-600 text-lg">
              {formatCurrency(totalIncome)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
