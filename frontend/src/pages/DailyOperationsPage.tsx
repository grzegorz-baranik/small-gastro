import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDailyRecord } from '../context/DailyRecordContext'
import { openDay, closeDay } from '../api/dailyRecords'
import { getTodaySales, createSale, deleteSale } from '../api/sales'
import { getProducts } from '../api/products'
import { getIngredients } from '../api/ingredients'
import { formatCurrency, getTodayDateString } from '../utils/formatters'
import { Play, Square, Trash2 } from 'lucide-react'
import LoadingSpinner from '../components/common/LoadingSpinner'
import type { Ingredient, InventorySnapshotCreate } from '../types'

export default function DailyOperationsPage() {
  const { todayRecord, isDayOpen, refetch } = useDailyRecord()
  const queryClient = useQueryClient()

  const { data: salesData, isLoading: salesLoading } = useQuery({
    queryKey: ['todaySales'],
    queryFn: getTodaySales,
    enabled: isDayOpen,
  })

  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: () => getProducts(true),
    enabled: isDayOpen,
  })

  const { data: ingredientsData } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
  })

  const createSaleMutation = useMutation({
    mutationFn: createSale,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['todaySales'] }),
  })

  const deleteSaleMutation = useMutation({
    mutationFn: deleteSale,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['todaySales'] }),
  })

  if (!todayRecord) {
    return (
      <OpenDayView
        ingredients={ingredientsData?.items || []}
        onSuccess={refetch}
      />
    )
  }

  if (!isDayOpen) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Operacje dzienne</h1>
        <div className="card text-center py-12">
          <p className="text-gray-600">Dzien jest zamkniety.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Operacje dzienne</h1>
        <CloseDayButton
          recordId={todayRecord.id}
          ingredients={ingredientsData?.items || []}
          onSuccess={refetch}
        />
      </div>

      {/* Sales Entry */}
      <div className="card">
        <h2 className="card-header">Dodaj sprzedaz</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {productsData?.items.map((product) => (
            <button
              key={product.id}
              onClick={() => createSaleMutation.mutate({ product_id: product.id, quantity_sold: 1 })}
              disabled={createSaleMutation.isPending}
              className="p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-left"
            >
              <p className="font-medium text-gray-900">{product.name}</p>
              <p className="text-primary-600 font-bold">{formatCurrency(product.price)}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Today's Sales */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="card-header mb-0">Dzisiejsza sprzedaz</h2>
          <div className="text-right">
            <p className="text-sm text-gray-500">Suma</p>
            <p className="text-xl font-bold text-primary-600">
              {formatCurrency(salesData?.total_revenue ?? 0)}
            </p>
          </div>
        </div>

        {salesLoading ? (
          <LoadingSpinner />
        ) : salesData?.items.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Brak sprzedazy</p>
        ) : (
          <div className="space-y-2">
            {salesData?.items.map((sale) => (
              <div key={sale.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{sale.product_name}</p>
                  <p className="text-sm text-gray-500">
                    {sale.quantity_sold} x {formatCurrency(sale.unit_price)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <p className="font-bold text-gray-900">{formatCurrency(sale.total_price)}</p>
                  <button
                    onClick={() => deleteSaleMutation.mutate(sale.id)}
                    className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function OpenDayView({ ingredients, onSuccess }: { ingredients: Ingredient[]; onSuccess: () => void }) {
  const [inventory, setInventory] = useState<Record<number, number>>({})
  const queryClient = useQueryClient()

  const openDayMutation = useMutation({
    mutationFn: openDay,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todayRecord'] })
      onSuccess()
    },
  })

  const handleOpenDay = () => {
    const openingInventory: InventorySnapshotCreate[] = Object.entries(inventory).map(([id, qty]) => {
      const ingredient = ingredients.find((i) => i.id === parseInt(id))
      return {
        ingredient_id: parseInt(id),
        quantity_grams: ingredient?.unit_type === 'weight' ? qty : undefined,
        quantity_count: ingredient?.unit_type === 'count' ? qty : undefined,
      }
    })

    openDayMutation.mutate({
      date: getTodayDateString(),
      opening_inventory: openingInventory,
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Otworz dzien</h1>

      <div className="card">
        <h2 className="card-header">Stany poczatkowe skladnikow</h2>
        <p className="text-sm text-gray-500 mb-4">
          Wprowadz ilosci skladnikow na poczatek dnia
        </p>

        <div className="space-y-3">
          {ingredients.map((ingredient) => (
            <div key={ingredient.id} className="flex items-center gap-4">
              <div className="flex-1">
                <p className="font-medium text-gray-900">{ingredient.name}</p>
                <p className="text-sm text-gray-500">
                  {ingredient.unit_type === 'weight' ? 'gramy' : 'sztuki'}
                </p>
              </div>
              <input
                type="number"
                min="0"
                step={ingredient.unit_type === 'weight' ? '0.01' : '1'}
                value={inventory[ingredient.id] || ''}
                onChange={(e) => setInventory({ ...inventory, [ingredient.id]: parseFloat(e.target.value) || 0 })}
                className="input w-32"
                placeholder="0"
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleOpenDay}
          disabled={openDayMutation.isPending}
          className="btn btn-primary w-full mt-6 flex items-center justify-center gap-2"
        >
          <Play className="w-4 h-4" />
          {openDayMutation.isPending ? 'Otwieranie...' : 'Otworz dzien'}
        </button>
      </div>
    </div>
  )
}

function CloseDayButton({ recordId, ingredients, onSuccess }: { recordId: number; ingredients: Ingredient[]; onSuccess: () => void }) {
  const [showModal, setShowModal] = useState(false)
  const [inventory, setInventory] = useState<Record<number, number>>({})
  const queryClient = useQueryClient()

  const closeDayMutation = useMutation({
    mutationFn: ({ closingInventory }: { closingInventory: InventorySnapshotCreate[] }) =>
      closeDay(recordId, closingInventory),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todayRecord'] })
      queryClient.invalidateQueries({ queryKey: ['todaySales'] })
      setShowModal(false)
      onSuccess()
    },
  })

  const handleCloseDay = () => {
    const closingInventory: InventorySnapshotCreate[] = Object.entries(inventory).map(([id, qty]) => {
      const ingredient = ingredients.find((i) => i.id === parseInt(id))
      return {
        ingredient_id: parseInt(id),
        quantity_grams: ingredient?.unit_type === 'weight' ? qty : undefined,
        quantity_count: ingredient?.unit_type === 'count' ? qty : undefined,
      }
    })

    closeDayMutation.mutate({ closingInventory })
  }

  return (
    <>
      <button onClick={() => setShowModal(true)} className="btn btn-secondary flex items-center gap-2">
        <Square className="w-4 h-4" />
        Zamknij dzien
      </button>

      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50" onClick={() => setShowModal(false)} />
            <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Zamknij dzien</h2>
              <p className="text-sm text-gray-500 mb-4">
                Wprowadz stany koncowe skladnikow
              </p>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {ingredients.map((ingredient) => (
                  <div key={ingredient.id} className="flex items-center gap-4">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{ingredient.name}</p>
                      <p className="text-sm text-gray-500">
                        {ingredient.unit_type === 'weight' ? 'gramy' : 'sztuki'}
                      </p>
                    </div>
                    <input
                      type="number"
                      min="0"
                      step={ingredient.unit_type === 'weight' ? '0.01' : '1'}
                      value={inventory[ingredient.id] || ''}
                      onChange={(e) => setInventory({ ...inventory, [ingredient.id]: parseFloat(e.target.value) || 0 })}
                      className="input w-32"
                      placeholder="0"
                    />
                  </div>
                ))}
              </div>

              <div className="flex gap-3 mt-6">
                <button onClick={() => setShowModal(false)} className="btn btn-secondary flex-1">
                  Anuluj
                </button>
                <button
                  onClick={handleCloseDay}
                  disabled={closeDayMutation.isPending}
                  className="btn btn-primary flex-1"
                >
                  {closeDayMutation.isPending ? 'Zamykanie...' : 'Zamknij dzien'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
