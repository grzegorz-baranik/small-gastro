import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCategoryTree, createCategory, deleteCategory } from '../api/categories'
import { Plus, Trash2, ChevronRight, ChevronDown, Tag, Folder, FolderOpen } from 'lucide-react'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import type { ExpenseCategory } from '../types'

const LEVEL_NAMES: Record<number, string> = {
  1: 'grupe glowna (poziom 1)',
  2: 'podgrupe (poziom 2)',
  3: 'kategorie koncowa (poziom 3)',
}

function getModalTitle(parentLevel: number | undefined): string {
  const newLevel = parentLevel !== undefined ? parentLevel + 1 : 1
  return `Dodaj ${LEVEL_NAMES[newLevel] || 'kategorie'}`
}

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
      queryClient.invalidateQueries({ queryKey: ['leafCategories'] })
      setShowModal(false)
      setParentId(undefined)
      setParentLevel(undefined)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categoryTree'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['leafCategories'] })
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || 'Nie udalo sie usunac kategorii'
      alert(message)
    },
  })

  const handleAddSubcategory = (parentCategoryId: number, parentLevel: number) => {
    setParentId(parentCategoryId)
    setParentLevel(parentLevel)
    setShowModal(true)
  }

  const [parentLevel, setParentLevel] = useState<number | undefined>()

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
              setParentLevel(undefined)
              setShowModal(true)
            }}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Dodaj grupe glowna
          </button>
        </div>

        {/* Hierarchy explanation */}
        <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-sm text-blue-800 mb-2 font-medium">Struktura kategorii (3 poziomy):</p>
          <div className="space-y-1 text-sm text-blue-700">
            <div className="flex items-center gap-2">
              <Folder className="w-4 h-4" />
              <span><strong>Poziom 1</strong> - Grupa glowna (np. Koszty operacyjne, Koszty administracyjne)</span>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <FolderOpen className="w-4 h-4" />
              <span><strong>Poziom 2</strong> - Podgrupa (np. Skladniki, Transport, Opakowania)</span>
            </div>
            <div className="flex items-center gap-2 ml-8">
              <Tag className="w-4 h-4" />
              <span><strong>Poziom 3</strong> - Kategoria koncowa <span className="bg-green-100 text-green-700 px-1.5 py-0.5 rounded text-xs">do przypisania</span></span>
            </div>
          </div>
          <p className="text-xs text-blue-600 mt-2">Tylko kategorie poziomu 3 mozna przypisac do transakcji.</p>
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
          setParentLevel(undefined)
        }}
        title={getModalTitle(parentLevel)}
      >
        <CategoryForm
          newLevel={parentLevel !== undefined ? parentLevel + 1 : 1}
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
  depth = 0,
}: {
  category: ExpenseCategory
  onAddSubcategory: (parentId: number, parentLevel: number) => void
  onDelete: (id: number) => void
  depth?: number
}) {
  const [isExpanded, setIsExpanded] = useState(true)
  const hasChildren = category.children && category.children.length > 0
  const canAddChild = category.level < 3
  const isLeaf = category.level === 3

  // Icons and colors based on level
  const getLevelIcon = () => {
    if (category.level === 1) return <Folder className="w-4 h-4 text-blue-500" />
    if (category.level === 2) return <FolderOpen className="w-4 h-4 text-amber-500" />
    return <Tag className="w-4 h-4 text-green-500" />
  }

  const getLevelBadge = () => {
    if (category.level === 1) return <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">grupa</span>
    if (category.level === 2) return <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">podgrupa</span>
    return <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">do przypisania</span>
  }

  return (
    <div>
      <div
        className={`flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors ${isLeaf ? 'bg-green-50/50' : ''}`}
        style={{ paddingLeft: `${depth * 24 + 12}px` }}
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
          {getLevelIcon()}
          <span className="font-medium text-gray-900">{category.name}</span>
          {getLevelBadge()}
        </div>
        <div className="flex items-center gap-2">
          {canAddChild && (
            <button
              onClick={() => onAddSubcategory(category.id, category.level)}
              className="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-gray-700"
              title={`Dodaj ${category.level === 1 ? 'podgrupe' : 'kategorie koncowa'}`}
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
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function CategoryForm({
  newLevel,
  onSubmit,
  isLoading,
}: {
  newLevel: number
  onSubmit: (name: string) => void
  isLoading: boolean
}) {
  const [name, setName] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isLoading || submitted || !name.trim()) return
    setSubmitted(true)
    onSubmit(name.trim())
  }

  const getLevelInfo = () => {
    if (newLevel === 1) {
      return {
        icon: <Folder className="w-5 h-5 text-blue-500" />,
        color: 'bg-blue-50 border-blue-200',
        textColor: 'text-blue-700',
        description: 'Grupa glowna sluzy do organizacji kategorii na najwyzszym poziomie (np. "Koszty operacyjne", "Koszty administracyjne").',
        placeholder: 'np. Koszty operacyjne',
      }
    }
    if (newLevel === 2) {
      return {
        icon: <FolderOpen className="w-5 h-5 text-amber-500" />,
        color: 'bg-amber-50 border-amber-200',
        textColor: 'text-amber-700',
        description: 'Podgrupa pozwala dalej podzielic kategorie (np. "Skladniki", "Transport", "Media").',
        placeholder: 'np. Skladniki, Transport',
      }
    }
    return {
      icon: <Tag className="w-5 h-5 text-green-500" />,
      color: 'bg-green-50 border-green-200',
      textColor: 'text-green-700',
      description: 'Kategoria koncowa to poziom, ktory mozna przypisac do transakcji (np. "Warzywa", "Mieso", "Paliwo").',
      placeholder: 'np. Warzywa, Mieso, Paliwo',
    }
  }

  const levelInfo = getLevelInfo()

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className={`p-3 rounded-lg border ${levelInfo.color}`}>
        <div className="flex items-center gap-2 mb-1">
          {levelInfo.icon}
          <span className={`font-medium ${levelInfo.textColor}`}>Poziom {newLevel}</span>
          {newLevel === 3 && (
            <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">do przypisania</span>
          )}
        </div>
        <p className={`text-sm ${levelInfo.textColor}`}>{levelInfo.description}</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Nazwa</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="input"
          placeholder={levelInfo.placeholder}
          required
        />
      </div>
      <button type="submit" className="btn btn-primary w-full" disabled={isLoading || submitted}>
        {isLoading || submitted ? 'Zapisywanie...' : 'Zapisz'}
      </button>
    </form>
  )
}
