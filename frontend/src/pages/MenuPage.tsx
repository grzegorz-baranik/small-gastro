import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProducts, createProduct, deleteProduct } from '../api/products'
import { getIngredients, createIngredient, deleteIngredient } from '../api/ingredients'
import { getVariants } from '../api/productVariants'
import { formatCurrency, formatQuantity } from '../utils/formatters'
import { Plus, Trash2, Package, Scale, Layers, Star } from 'lucide-react'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import VariantManagementModal from '../components/products/VariantManagementModal'
import type { Product, ProductCreate, IngredientCreate, ProductVariant } from '../types'

export default function MenuPage() {
  const [activeTab, setActiveTab] = useState<'products' | 'ingredients'>('products')
  const [showProductModal, setShowProductModal] = useState(false)
  const [showIngredientModal, setShowIngredientModal] = useState(false)
  const [selectedProductForVariants, setSelectedProductForVariants] = useState<Product | null>(null)

  const queryClient = useQueryClient()

  const { data: productsData, isLoading: productsLoading } = useQuery({
    queryKey: ['products'],
    queryFn: () => getProducts(false),
  })

  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
  })

  const createProductMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setShowProductModal(false)
    },
  })

  const deleteProductMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
  })

  const createIngredientMutation = useMutation({
    mutationFn: createIngredient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingredients'] })
      setShowIngredientModal(false)
    },
  })

  const deleteIngredientMutation = useMutation({
    mutationFn: deleteIngredient,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ingredients'] }),
  })

  const handleDeleteProduct = (product: Product) => {
    if (window.confirm(`Czy na pewno chcesz dezaktywowac produkt "${product.name}"?`)) {
      deleteProductMutation.mutate(product.id)
    }
  }

  const handleDeleteIngredient = (ingredientId: number, ingredientName: string) => {
    if (window.confirm(`Czy na pewno chcesz usunac skladnik "${ingredientName}"?`)) {
      deleteIngredientMutation.mutate(ingredientId)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Menu</h1>
        <button
          onClick={() => activeTab === 'products' ? setShowProductModal(true) : setShowIngredientModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          {activeTab === 'products' ? 'Dodaj produkt' : 'Dodaj skladnik'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('products')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'products'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Produkty
        </button>
        <button
          onClick={() => setActiveTab('ingredients')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'ingredients'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Skladniki
        </button>
      </div>

      {/* Products List */}
      {activeTab === 'products' && (
        <div className="space-y-4">
          {productsLoading ? (
            <LoadingSpinner />
          ) : productsData?.items.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>Brak produktow w menu.</p>
              <p className="text-sm mt-1">Dodaj pierwszy produkt powyzej.</p>
            </div>
          ) : (
            productsData?.items.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onManageVariants={() => setSelectedProductForVariants(product)}
                onDelete={() => handleDeleteProduct(product)}
              />
            ))
          )}
        </div>
      )}

      {/* Ingredients List */}
      {activeTab === 'ingredients' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ingredientsLoading ? (
            <LoadingSpinner />
          ) : ingredientsData?.items.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              <p>Brak skladnikow.</p>
              <p className="text-sm mt-1">Dodaj pierwszy skladnik powyzej.</p>
            </div>
          ) : (
            ingredientsData?.items.map((ingredient) => (
              <div key={ingredient.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${ingredient.unit_type === 'weight' ? 'bg-blue-100' : 'bg-purple-100'}`}>
                      {ingredient.unit_type === 'weight' ? (
                        <Scale className="w-4 h-4 text-blue-600" />
                      ) : (
                        <Package className="w-4 h-4 text-purple-600" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{ingredient.name}</h3>
                      <p className="text-sm text-gray-500">
                        {ingredient.unit_type === 'weight' ? 'Na wage' : 'Na sztuki'}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteIngredient(ingredient.id, ingredient.name)}
                    className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Add Product Modal */}
      <Modal
        isOpen={showProductModal}
        onClose={() => setShowProductModal(false)}
        title="Dodaj produkt"
      >
        <ProductForm
          onSubmit={(data) => createProductMutation.mutate(data)}
          isLoading={createProductMutation.isPending}
        />
      </Modal>

      {/* Add Ingredient Modal */}
      <Modal
        isOpen={showIngredientModal}
        onClose={() => setShowIngredientModal(false)}
        title="Dodaj skladnik"
      >
        <IngredientForm
          onSubmit={(data) => createIngredientMutation.mutate(data)}
          isLoading={createIngredientMutation.isPending}
        />
      </Modal>

      {/* Variant Management Modal */}
      {selectedProductForVariants && (
        <VariantManagementModal
          isOpen={true}
          onClose={() => setSelectedProductForVariants(null)}
          product={selectedProductForVariants}
        />
      )}
    </div>
  )
}

// Product Card Component with Variants
function ProductCard({
  product,
  onManageVariants,
  onDelete,
}: {
  product: Product
  onManageVariants: () => void
  onDelete: () => void
}) {
  const { data: variantsData, isLoading: variantsLoading } = useQuery({
    queryKey: ['productVariants', product.id],
    queryFn: () => getVariants(product.id, true),
  })

  const variants = variantsData?.items || []
  const hasVariants = variants.length > 0
  const defaultVariant = variants.find((v) => v.is_default)
  const displayPrice = hasVariants
    ? defaultVariant?.price ?? variants[0]?.price ?? product.price
    : product.price

  return (
    <div className={`card ${!product.is_active ? 'opacity-50' : ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h3 className="font-semibold text-gray-900">{product.name}</h3>
            {!product.is_active && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                Nieaktywny
              </span>
            )}
            {hasVariants && (
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded flex items-center gap-1">
                <Layers className="w-3 h-3" />
                {variants.length} {variants.length === 1 ? 'wariant' : variants.length < 5 ? 'warianty' : 'wariantow'}
              </span>
            )}
          </div>

          {/* Price display */}
          {hasVariants ? (
            <div className="mt-2">
              {variantsLoading ? (
                <p className="text-sm text-gray-400">Ladowanie wariantow...</p>
              ) : (
                <VariantPriceList variants={variants} />
              )}
            </div>
          ) : (
            <p className="text-lg font-bold text-primary-600 mt-1">
              {formatCurrency(displayPrice)}
            </p>
          )}

          {/* Legacy ingredients display (for backward compatibility) */}
          {product.ingredients.length > 0 && !hasVariants && (
            <div className="mt-3 space-y-1">
              <p className="text-sm text-gray-500">Skladniki:</p>
              <div className="flex flex-wrap gap-2">
                {product.ingredients.map((pi) => (
                  <span
                    key={pi.id}
                    className="text-sm bg-gray-100 text-gray-700 px-2 py-1 rounded"
                  >
                    {pi.ingredient_name}: {formatQuantity(pi.quantity, pi.ingredient_unit_type || 'weight')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={onManageVariants}
            className="p-2 hover:bg-blue-100 rounded-lg transition-colors"
            title="Zarzadzaj wariantami"
          >
            <Layers className="w-4 h-4 text-blue-600" />
          </button>
          <button
            onClick={onDelete}
            className="p-2 hover:bg-red-100 rounded-lg transition-colors"
            title="Dezaktywuj produkt"
          >
            <Trash2 className="w-4 h-4 text-red-600" />
          </button>
        </div>
      </div>
    </div>
  )
}

// Component to display variant prices in a compact list
function VariantPriceList({ variants }: { variants: ProductVariant[] }) {
  const sortedVariants = [...variants].sort((a, b) => {
    // Default variant first
    if (a.is_default && !b.is_default) return -1
    if (!a.is_default && b.is_default) return 1
    // Then by price
    return a.price - b.price
  })

  return (
    <div className="flex flex-wrap gap-2">
      {sortedVariants.map((variant) => (
        <div
          key={variant.id}
          className={`flex items-center gap-1 px-2 py-1 rounded text-sm ${
            variant.is_default
              ? 'bg-primary-100 text-primary-700 font-medium'
              : 'bg-gray-100 text-gray-700'
          }`}
        >
          {variant.is_default && <Star className="w-3 h-3 fill-current" />}
          <span>{variant.name}</span>
          <span className="font-semibold">{formatCurrency(variant.price)}</span>
        </div>
      ))}
    </div>
  )
}

function ProductForm({ onSubmit, isLoading }: { onSubmit: (data: ProductCreate) => void; isLoading: boolean }) {
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({ name, price: parseFloat(price) })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Nazwa</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="input"
          placeholder="np. Kebab, Burger"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Cena domyslna (PLN)</label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          className="input"
          required
        />
        <p className="text-xs text-gray-500 mt-1">
          Mozesz dodac warianty z roznymi cenami po utworzeniu produktu.
        </p>
      </div>
      <button type="submit" className="btn btn-primary w-full" disabled={isLoading}>
        {isLoading ? 'Zapisywanie...' : 'Zapisz'}
      </button>
    </form>
  )
}

function IngredientForm({ onSubmit, isLoading }: { onSubmit: (data: IngredientCreate) => void; isLoading: boolean }) {
  const [name, setName] = useState('')
  const [unitType, setUnitType] = useState<'weight' | 'count'>('weight')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({ name, unit_type: unitType })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Nazwa</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="input"
          placeholder="np. Mieso, Bulka, Sos"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Typ jednostki</label>
        <select
          value={unitType}
          onChange={(e) => setUnitType(e.target.value as 'weight' | 'count')}
          className="input"
        >
          <option value="weight">Na wage (gramy)</option>
          <option value="count">Na sztuki</option>
        </select>
      </div>
      <button type="submit" className="btn btn-primary w-full" disabled={isLoading}>
        {isLoading ? 'Zapisywanie...' : 'Zapisz'}
      </button>
    </form>
  )
}
