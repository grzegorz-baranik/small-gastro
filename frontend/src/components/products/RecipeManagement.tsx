import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Star, X, Check } from 'lucide-react'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import {
  getVariantIngredients,
  addVariantIngredient,
  updateVariantIngredient,
  removeVariantIngredient,
} from '../../api/productVariants'
import { getIngredients } from '../../api/ingredients'
import { formatQuantity } from '../../utils/formatters'
import type {
  ProductVariant,
  VariantIngredient,
  VariantIngredientCreate,
  VariantIngredientUpdate,
  Ingredient,
} from '../../types'

interface RecipeManagementProps {
  isOpen: boolean
  onClose: () => void
  variant: ProductVariant
  productName: string
}

export default function RecipeManagement({
  isOpen,
  onClose,
  variant,
  productName,
}: RecipeManagementProps) {
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingIngredient, setEditingIngredient] = useState<VariantIngredient | null>(null)

  const queryClient = useQueryClient()

  const { data: ingredientsData, isLoading: ingredientsLoading } = useQuery({
    queryKey: ['variantIngredients', variant.id],
    queryFn: () => getVariantIngredients(variant.id),
    enabled: isOpen,
  })

  const { data: allIngredients } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
    enabled: isOpen,
  })

  const addMutation = useMutation({
    mutationFn: (data: VariantIngredientCreate) => addVariantIngredient(variant.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variantIngredients', variant.id] })
      setShowAddForm(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({
      ingredientId,
      data,
    }: {
      ingredientId: number
      data: VariantIngredientUpdate
    }) => updateVariantIngredient(variant.id, ingredientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variantIngredients', variant.id] })
      setEditingIngredient(null)
    },
  })

  const removeMutation = useMutation({
    mutationFn: (ingredientId: number) => removeVariantIngredient(variant.id, ingredientId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variantIngredients', variant.id] })
    },
  })

  const handleRemove = (ingredient: VariantIngredient) => {
    if (
      window.confirm(
        `Czy na pewno chcesz usunac "${ingredient.ingredient_name}" z przepisu?`
      )
    ) {
      removeMutation.mutate(ingredient.ingredient_id)
    }
  }

  const handleTogglePrimary = (ingredient: VariantIngredient) => {
    updateMutation.mutate({
      ingredientId: ingredient.ingredient_id,
      data: { is_primary: !ingredient.is_primary },
    })
  }

  // Get list of ingredients not yet in the recipe
  const availableIngredients =
    allIngredients?.items.filter(
      (ing) =>
        !ingredientsData?.items.some(
          (vi) => vi.ingredient_id === ing.id
        )
    ) || []

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Przepis: ${productName} - ${variant.name}`}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Zarzadzaj skladnikami w przepisie
          </p>
          {availableIngredients.length > 0 && (
            <button
              onClick={() => setShowAddForm(true)}
              className="btn btn-primary flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" />
              Dodaj skladnik
            </button>
          )}
        </div>

        {/* Add ingredient form */}
        {showAddForm && (
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <AddIngredientForm
              availableIngredients={availableIngredients}
              onSubmit={(data) => addMutation.mutate(data)}
              onCancel={() => setShowAddForm(false)}
              isLoading={addMutation.isPending}
            />
          </div>
        )}

        {/* Ingredients list */}
        {ingredientsLoading ? (
          <LoadingSpinner />
        ) : ingredientsData?.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>Brak skladnikow w przepisie.</p>
            <p className="text-sm mt-1">Dodaj pierwszy skladnik powyzej.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {ingredientsData?.items.map((ingredient) => (
              <div
                key={ingredient.id}
                className="card p-3 hover:bg-gray-50 transition-colors"
              >
                {editingIngredient?.id === ingredient.id ? (
                  <EditIngredientForm
                    ingredient={ingredient}
                    onSubmit={(data) =>
                      updateMutation.mutate({
                        ingredientId: ingredient.ingredient_id,
                        data,
                      })
                    }
                    onCancel={() => setEditingIngredient(null)}
                    isLoading={updateMutation.isPending}
                  />
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleTogglePrimary(ingredient)}
                        className={`p-1.5 rounded-lg transition-colors ${
                          ingredient.is_primary
                            ? 'bg-yellow-100 text-yellow-600'
                            : 'bg-gray-100 text-gray-400 hover:text-yellow-600'
                        }`}
                        title={
                          ingredient.is_primary
                            ? 'Skladnik glowny'
                            : 'Oznacz jako glowny'
                        }
                      >
                        <Star
                          className={`w-4 h-4 ${
                            ingredient.is_primary ? 'fill-current' : ''
                          }`}
                        />
                      </button>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {ingredient.ingredient_name}
                          </span>
                          {ingredient.is_primary && (
                            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                              Glowny
                            </span>
                          )}
                        </div>
                        <span className="text-sm text-gray-500">
                          {formatQuantity(
                            ingredient.quantity,
                            ingredient.ingredient_unit_type || 'weight'
                          )}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setEditingIngredient(ingredient)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-sm text-primary-600"
                      >
                        Edytuj
                      </button>
                      <button
                        onClick={() => handleRemove(ingredient)}
                        className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Legend */}
        <div className="pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            <Star className="w-3 h-3 inline mr-1 text-yellow-600" />
            Skladnik glowny - uzywany do obliczen marzy i raportow
          </p>
        </div>
      </div>
    </Modal>
  )
}

// Form for adding new ingredient to recipe
function AddIngredientForm({
  availableIngredients,
  onSubmit,
  onCancel,
  isLoading,
}: {
  availableIngredients: Ingredient[]
  onSubmit: (data: VariantIngredientCreate) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [ingredientId, setIngredientId] = useState<number | ''>('')
  const [quantity, setQuantity] = useState('')
  const [isPrimary, setIsPrimary] = useState(false)

  const selectedIngredient = availableIngredients.find(
    (ing) => ing.id === ingredientId
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (ingredientId === '') return
    onSubmit({
      ingredient_id: ingredientId as number,
      quantity: parseFloat(quantity),
      is_primary: isPrimary,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h4 className="font-medium text-gray-900">Dodaj skladnik do przepisu</h4>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Skladnik
          </label>
          <select
            value={ingredientId}
            onChange={(e) =>
              setIngredientId(e.target.value ? parseInt(e.target.value) : '')
            }
            className="input"
            required
          >
            <option value="">Wybierz skladnik...</option>
            {availableIngredients.map((ing) => (
              <option key={ing.id} value={ing.id}>
                {ing.name} ({ing.unit_type === 'weight' ? 'g' : 'szt.'})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ilosc ({selectedIngredient?.unit_type === 'weight' ? 'gramy' : 'sztuki'})
          </label>
          <input
            type="number"
            step={selectedIngredient?.unit_type === 'weight' ? '0.1' : '1'}
            min="0.1"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            className="input"
            required
          />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="isPrimary"
          checked={isPrimary}
          onChange={(e) => setIsPrimary(e.target.checked)}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label htmlFor="isPrimary" className="text-sm text-gray-700">
          Oznacz jako skladnik glowny
        </label>
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel} className="btn btn-secondary">
          Anuluj
        </button>
        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? 'Dodawanie...' : 'Dodaj'}
        </button>
      </div>
    </form>
  )
}

// Form for editing ingredient quantity
function EditIngredientForm({
  ingredient,
  onSubmit,
  onCancel,
  isLoading,
}: {
  ingredient: VariantIngredient
  onSubmit: (data: VariantIngredientUpdate) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [quantity, setQuantity] = useState(ingredient.quantity.toString())

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({ quantity: parseFloat(quantity) })
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-3">
      <span className="font-medium text-gray-900 flex-shrink-0">
        {ingredient.ingredient_name}
      </span>
      <input
        type="number"
        step={ingredient.ingredient_unit_type === 'weight' ? '0.1' : '1'}
        min="0.1"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        className="input w-24"
        required
      />
      <span className="text-sm text-gray-500">
        {ingredient.ingredient_unit_type === 'weight' ? 'g' : 'szt.'}
      </span>
      <div className="flex gap-1 ml-auto">
        <button
          type="button"
          onClick={onCancel}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <X className="w-4 h-4 text-gray-600" />
        </button>
        <button
          type="submit"
          className="p-2 hover:bg-green-100 rounded-lg"
          disabled={isLoading}
        >
          <Check className="w-4 h-4 text-green-600" />
        </button>
      </div>
    </form>
  )
}
