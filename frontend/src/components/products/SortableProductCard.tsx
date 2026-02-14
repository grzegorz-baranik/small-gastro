import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Trash2, Layers, Star } from 'lucide-react'
import { formatCurrency, formatQuantity } from '../../utils/formatters'
import type { Product, ProductVariantInProduct } from '../../types'

interface SortableProductCardProps {
  product: Product
  onManageVariants: () => void
  onDelete: () => void
  'data-testid'?: string
}

export default function SortableProductCard({
  product,
  onManageVariants,
  onDelete,
  'data-testid': dataTestId,
}: SortableProductCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: product.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.8 : 1,
    zIndex: isDragging ? 1000 : 'auto',
  }

  const variants = product.variants || []
  const hasVariants = variants.length > 1
  const defaultVariant = variants[0]
  const displayPrice = defaultVariant?.price_pln ?? 0
  const ingredients = defaultVariant?.ingredients || []

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`card ${isDragging ? 'shadow-lg ring-2 ring-primary-300' : ''} ${!product.is_active ? 'opacity-50' : ''}`}
      data-testid={dataTestId}
    >
      <div className="flex items-start gap-3">
        {/* Drag handle */}
        <button
          {...attributes}
          {...listeners}
          className="p-2 hover:bg-gray-100 rounded cursor-grab active:cursor-grabbing touch-none"
          aria-label="Przeciagnij aby zmienic kolejnosc"
        >
          <GripVertical className="w-4 h-4 text-gray-400" />
        </button>

        {/* Product content */}
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
              <VariantPriceList variants={variants} />
            </div>
          ) : (
            <p className="text-lg font-bold text-primary-600 mt-1">
              {formatCurrency(displayPrice)}
            </p>
          )}

          {/* Ingredients display from first variant */}
          {ingredients.length > 0 && !hasVariants && (
            <div className="mt-3 space-y-1">
              <p className="text-sm text-gray-500">Skladniki:</p>
              <div className="flex flex-wrap gap-2">
                {ingredients.map((pi) => (
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

        {/* Action buttons */}
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

function VariantPriceList({ variants }: { variants: ProductVariantInProduct[] }) {
  const sortedVariants = [...variants].sort((a, b) => a.price_pln - b.price_pln)

  return (
    <div className="flex flex-wrap gap-2">
      {sortedVariants.map((variant, index) => (
        <div
          key={variant.id}
          className={`flex items-center gap-1 px-2 py-1 rounded text-sm ${
            index === 0
              ? 'bg-primary-100 text-primary-700 font-medium'
              : 'bg-gray-100 text-gray-700'
          }`}
        >
          {index === 0 && <Star className="w-3 h-3 fill-current" />}
          <span>{variant.name || 'Domyslny'}</span>
          <span className="font-semibold">{formatCurrency(variant.price_pln)}</span>
        </div>
      ))}
    </div>
  )
}
