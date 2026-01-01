import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Edit, ChefHat, Star, X, Check } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import RecipeManagement from './RecipeManagement'
import { getVariants, createVariant, updateVariant, deleteVariant } from '../../api/productVariants'
import { formatCurrency } from '../../utils/formatters'
import type { Product, ProductVariant, ProductVariantCreate, ProductVariantUpdate } from '../../types'

interface VariantManagementModalProps {
  isOpen: boolean
  onClose: () => void
  product: Product
}

export default function VariantManagementModal({
  isOpen,
  onClose,
  product,
}: VariantManagementModalProps) {
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingVariant, setEditingVariant] = useState<ProductVariant | null>(null)
  const [selectedVariantForRecipe, setSelectedVariantForRecipe] = useState<ProductVariant | null>(null)

  const queryClient = useQueryClient()

  const { data: variantsData, isLoading } = useQuery({
    queryKey: ['productVariants', product.id],
    queryFn: () => getVariants(product.id, false),
    enabled: isOpen,
  })

  const createMutation = useMutation({
    mutationFn: (data: ProductVariantCreate) => createVariant(product.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productVariants', product.id] })
      setShowAddForm(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ variantId, data }: { variantId: number; data: ProductVariantUpdate }) =>
      updateVariant(product.id, variantId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productVariants', product.id] })
      setEditingVariant(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (variantId: number) => deleteVariant(product.id, variantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productVariants', product.id] })
    },
  })

  const handleDelete = (variant: ProductVariant) => {
    if (window.confirm(`Czy na pewno chcesz dezaktywowac wariant "${variant.name}"?`)) {
      deleteMutation.mutate(variant.id)
    }
  }

  const handleSetDefault = (variant: ProductVariant) => {
    updateMutation.mutate({
      variantId: variant.id,
      data: { is_default: true },
    })
  }

  // If recipe management modal is open
  if (selectedVariantForRecipe) {
    return (
      <RecipeManagement
        isOpen={true}
        onClose={() => setSelectedVariantForRecipe(null)}
        variant={selectedVariantForRecipe}
        productName={product.name}
      />
    )
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Warianty: ${product.name}`}
    >
      <div className="space-y-4">
        {/* Header with add button */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Zarzadzaj wariantami produktu i ich przepisami
          </p>
          <button
            onClick={() => setShowAddForm(true)}
            className="btn btn-primary flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Dodaj wariant
          </button>
        </div>

        {/* Add variant form */}
        {showAddForm && (
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <VariantForm
              onSubmit={(data) => createMutation.mutate(data)}
              onCancel={() => setShowAddForm(false)}
              isLoading={createMutation.isPending}
            />
          </div>
        )}

        {/* Variants list */}
        {isLoading ? (
          <LoadingSpinner />
        ) : variantsData?.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>Brak wariantow dla tego produktu.</p>
            <p className="text-sm mt-1">Dodaj pierwszy wariant powyzej.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {variantsData?.items.map((variant) => (
              <div
                key={variant.id}
                className={`card p-4 ${!variant.is_active ? 'opacity-50 bg-gray-50' : ''}`}
              >
                {editingVariant?.id === variant.id ? (
                  <VariantEditForm
                    variant={variant}
                    onSubmit={(data) =>
                      updateMutation.mutate({ variantId: variant.id, data })
                    }
                    onCancel={() => setEditingVariant(null)}
                    isLoading={updateMutation.isPending}
                  />
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900">{variant.name}</h4>
                          {variant.is_default && (
                            <span className="inline-flex items-center gap-1 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                              <Star className="w-3 h-3" />
                              Domyslny
                            </span>
                          )}
                          {!variant.is_active && (
                            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                              Nieaktywny
                            </span>
                          )}
                        </div>
                        <p className="text-lg font-bold text-primary-600">
                          {formatCurrency(variant.price)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {!variant.is_default && variant.is_active && (
                        <button
                          onClick={() => handleSetDefault(variant)}
                          className="p-2 hover:bg-yellow-100 rounded-lg transition-colors"
                          title="Ustaw jako domyslny"
                        >
                          <Star className="w-4 h-4 text-yellow-600" />
                        </button>
                      )}
                      <button
                        onClick={() => setSelectedVariantForRecipe(variant)}
                        className="p-2 hover:bg-blue-100 rounded-lg transition-colors"
                        title="Zarzadzaj przepisem"
                      >
                        <ChefHat className="w-4 h-4 text-blue-600" />
                      </button>
                      <button
                        onClick={() => setEditingVariant(variant)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Edytuj"
                      >
                        <Edit className="w-4 h-4 text-gray-600" />
                      </button>
                      {variant.is_active && (
                        <button
                          onClick={() => handleDelete(variant)}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                          title="Dezaktywuj"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  )
}

// Form for adding new variant
function VariantForm({
  onSubmit,
  onCancel,
  isLoading,
}: {
  onSubmit: (data: ProductVariantCreate) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [isDefault, setIsDefault] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      name,
      price: parseFloat(price),
      is_default: isDefault,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h4 className="font-medium text-gray-900">Nowy wariant</h4>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nazwa wariantu
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input"
            placeholder="np. Maly, Duzy, XL"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Cena (PLN)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="input"
            required
          />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="isDefault"
          checked={isDefault}
          onChange={(e) => setIsDefault(e.target.checked)}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label htmlFor="isDefault" className="text-sm text-gray-700">
          Ustaw jako domyslny wariant
        </label>
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel} className="btn btn-secondary">
          Anuluj
        </button>
        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? 'Zapisywanie...' : 'Dodaj'}
        </button>
      </div>
    </form>
  )
}

// Form for editing existing variant
function VariantEditForm({
  variant,
  onSubmit,
  onCancel,
  isLoading,
}: {
  variant: ProductVariant
  onSubmit: (data: ProductVariantUpdate) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [name, setName] = useState(variant.name)
  const [price, setPrice] = useState(variant.price.toString())

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      name,
      price: parseFloat(price),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nazwa
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Cena (PLN)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="input"
            required
          />
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel} className="p-2 hover:bg-gray-100 rounded-lg">
          <X className="w-4 h-4 text-gray-600" />
        </button>
        <button type="submit" className="p-2 hover:bg-green-100 rounded-lg" disabled={isLoading}>
          <Check className="w-4 h-4 text-green-600" />
        </button>
      </div>
    </form>
  )
}
