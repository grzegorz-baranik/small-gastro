import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTransactions, createTransaction, deleteTransaction } from '../api/transactions'
import { getCategories } from '../api/categories'
import { formatCurrency, formatDate } from '../utils/formatters'
import { Plus, Trash2, TrendingUp, TrendingDown } from 'lucide-react'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import type { TransactionCreate, TransactionType, PaymentMethod } from '../types'

const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  cash: 'Gotowka',
  card: 'Karta',
  bank_transfer: 'Przelew',
}

export default function FinancesPage() {
  const [showModal, setShowModal] = useState(false)
  const [typeFilter, setTypeFilter] = useState<TransactionType | ''>('')
  const queryClient = useQueryClient()

  const { data: transactionsData, isLoading } = useQuery({
    queryKey: ['transactions', typeFilter],
    queryFn: () => getTransactions(typeFilter ? { type_filter: typeFilter } : undefined),
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const createMutation = useMutation({
    mutationFn: createTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setShowModal(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Finanse</h1>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Dodaj transakcje
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <button
          onClick={() => setTypeFilter('')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            typeFilter === '' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Wszystkie
        </button>
        <button
          onClick={() => setTypeFilter('revenue')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            typeFilter === 'revenue' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Przychody
        </button>
        <button
          onClick={() => setTypeFilter('expense')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            typeFilter === 'expense' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Wydatki
        </button>
      </div>

      {/* Transactions List */}
      <div className="card">
        {isLoading ? (
          <LoadingSpinner />
        ) : transactionsData?.items.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Brak transakcji</p>
        ) : (
          <div className="space-y-3">
            {transactionsData?.items.map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-4 border border-gray-100 rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg ${transaction.type === 'revenue' ? 'bg-green-100' : 'bg-red-100'}`}>
                    {transaction.type === 'revenue' ? (
                      <TrendingUp className="w-5 h-5 text-green-600" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {transaction.description || (transaction.type === 'revenue' ? 'Przychod' : 'Wydatek')}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatDate(transaction.transaction_date)} • {PAYMENT_METHOD_LABELS[transaction.payment_method]}
                      {transaction.category_name && ` • ${transaction.category_name}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <p className={`text-lg font-bold ${transaction.type === 'revenue' ? 'text-green-600' : 'text-red-600'}`}>
                    {transaction.type === 'revenue' ? '+' : '-'}{formatCurrency(transaction.amount)}
                  </p>
                  <button
                    onClick={() => deleteMutation.mutate(transaction.id)}
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

      {/* Add Transaction Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Dodaj transakcje"
      >
        <TransactionForm
          categories={categories || []}
          onSubmit={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
        />
      </Modal>
    </div>
  )
}

function TransactionForm({
  categories,
  onSubmit,
  isLoading,
}: {
  categories: { id: number; name: string }[]
  onSubmit: (data: TransactionCreate) => void
  isLoading: boolean
}) {
  const [type, setType] = useState<TransactionType>('expense')
  const [amount, setAmount] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash')
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [description, setDescription] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      type,
      amount: parseFloat(amount),
      payment_method: paymentMethod,
      category_id: type === 'expense' ? categoryId : undefined,
      description: description || undefined,
      transaction_date: date,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Typ</label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setType('revenue')}
            className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
              type === 'revenue' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Przychod
          </button>
          <button
            type="button"
            onClick={() => setType('expense')}
            className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
              type === 'expense' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Wydatek
          </button>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Kwota (PLN)</label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="input"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Metoda platnosci</label>
        <select
          value={paymentMethod}
          onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
          className="input"
        >
          <option value="cash">Gotowka</option>
          <option value="card">Karta</option>
          <option value="bank_transfer">Przelew bankowy</option>
        </select>
      </div>

      {type === 'expense' && categories.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Kategoria</label>
          <select
            value={categoryId || ''}
            onChange={(e) => setCategoryId(e.target.value ? parseInt(e.target.value) : undefined)}
            className="input"
          >
            <option value="">Bez kategorii</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Data</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="input"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Opis (opcjonalny)</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="input"
        />
      </div>

      <button type="submit" className="btn btn-primary w-full" disabled={isLoading}>
        {isLoading ? 'Zapisywanie...' : 'Zapisz'}
      </button>
    </form>
  )
}
