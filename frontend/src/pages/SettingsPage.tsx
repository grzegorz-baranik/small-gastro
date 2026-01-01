import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCategoryTree, createCategory, deleteCategory } from '../api/categories'
import { Plus, Trash2, ChevronRight, ChevronDown } from 'lucide-react'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import type { ExpenseCategory } from '../types'

export default function SettingsPage() {
  const [showModal, setShowModal] = useState(false)
  const [parentId, setParentId] = useState<number | undefined>()
  const queryClient = useQueryClient()

  const { data: categoryTree, isLoading } = useQuery({
    queryKey: ['categoryTree'],
    queryFn: getCategoryTree,
  })

  const createMutation = useMutation({
    mutationFn: createCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categoryTree'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setShowModal(false)
      setParentId(undefined)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categoryTree'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })

  const handleAddSubcategory = (parentCategoryId: number) => {
    setParentId(parentCategoryId)
    setShowModal(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Ustawienia</h1>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="card-header mb-0">Kategorie wydatkow</h2>
          <button
            onClick={() => {
              setParentId(undefined)
              setShowModal(true)
            }}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Dodaj kategorie
          </button>
        </div>

        {isLoading ? (
          <LoadingSpinner />
        ) : categoryTree?.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            Brak kategorii. Dodaj pierwsza kategorie wydatkow.
          </p>
        ) : (
          <div className="space-y-2">
            {categoryTree?.map((category) => (
              <CategoryTreeItem
                key={category.id}
                category={category}
                onAddSubcategory={handleAddSubcategory}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))}
          </div>
        )}
      </div>

      <Modal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false)
          setParentId(undefined)
        }}
        title={parentId ? 'Dodaj podkategorie' : 'Dodaj kategorie'}
      >
        <CategoryForm
          parentId={parentId}
          onSubmit={(name) => createMutation.mutate({ name, parent_id: parentId })}
          isLoading={createMutation.isPending}
        />
      </Modal>
    </div>
  )
}

function CategoryTreeItem({
  category,
  onAddSubcategory,
  onDelete,
  level = 0,
}: {
  category: ExpenseCategory
  onAddSubcategory: (parentId: number) => void
  onDelete: (id: number) => void
  level?: number
}) {
  const [isExpanded, setIsExpanded] = useState(true)
  const hasChildren = category.children && category.children.length > 0
  const canAddChild = category.level < 3

  return (
    <div>
      <div
        className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors"
        style={{ paddingLeft: `${level * 24 + 12}px` }}
      >
        <div className="flex items-center gap-2">
          {hasChildren ? (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-gray-200 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-500" />
              )}
            </button>
          ) : (
            <div className="w-6" />
          )}
          <span className="font-medium text-gray-900">{category.name}</span>
          <span className="text-xs text-gray-400">poziom {category.level}</span>
        </div>
        <div className="flex items-center gap-2">
          {canAddChild && (
            <button
              onClick={() => onAddSubcategory(category.id)}
              className="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-gray-700"
              title="Dodaj podkategorie"
            >
              <Plus className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => onDelete(category.id)}
            className="p-1 hover:bg-red-100 rounded text-gray-500 hover:text-red-600"
            title="Usun"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      {isExpanded && hasChildren && (
        <div>
          {category.children?.map((child) => (
            <CategoryTreeItem
              key={child.id}
              category={child}
              onAddSubcategory={onAddSubcategory}
              onDelete={onDelete}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function CategoryForm({
  parentId: _parentId,
  onSubmit,
  isLoading,
}: {
  parentId?: number
  onSubmit: (name: string) => void
  isLoading: boolean
}) {
  const [name, setName] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(name)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Nazwa kategorii</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="input"
          placeholder="np. Skladniki, Transport, Opakowania"
          required
        />
      </div>
      <button type="submit" className="btn btn-primary w-full" disabled={isLoading}>
        {isLoading ? 'Zapisywanie...' : 'Zapisz'}
      </button>
    </form>
  )
}
