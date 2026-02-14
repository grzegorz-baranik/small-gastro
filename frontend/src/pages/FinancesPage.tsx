import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTransactions, createTransaction, deleteTransaction } from '../api/transactions'
import { getLeafCategories } from '../api/categories'
import { getEmployees } from '../api/employees'
import { calculateHoursForPeriod } from '../api/wageAnalytics'
import { formatCurrency, formatDate } from '../utils/formatters'
import { Plus, Trash2, TrendingUp, TrendingDown, Calculator, User } from 'lucide-react'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import SearchableSelect from '../components/common/SearchableSelect'
import type { TransactionCreate, TransactionType, PaymentMethod, WagePeriodType, LeafCategory } from '../types'

export default function FinancesPage() {
  const { t } = useTranslation()
  const [showModal, setShowModal] = useState(false)
  const [typeFilter, setTypeFilter] = useState<TransactionType | ''>('')
  const queryClient = useQueryClient()

  const { data: transactionsData, isLoading } = useQuery({
    queryKey: ['transactions', typeFilter],
    queryFn: () => getTransactions(typeFilter ? { type_filter: typeFilter } : undefined),
  })

  const { data: leafCategories } = useQuery({
    queryKey: ['leafCategories'],
    queryFn: getLeafCategories,
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
        <h1 className="text-2xl font-bold text-gray-900">{t('finances.title')}</h1>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
          data-testid="add-expense-btn"
        >
          <Plus className="w-4 h-4" />
          {t('finances.addTransaction')}
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
          {t('finances.filterAll')}
        </button>
        <button
          onClick={() => setTypeFilter('revenue')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            typeFilter === 'revenue' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {t('finances.filterRevenue')}
        </button>
        <button
          onClick={() => setTypeFilter('expense')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            typeFilter === 'expense' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {t('finances.filterExpenses')}
        </button>
      </div>

      {/* Transactions List */}
      <div className="card">
        {isLoading ? (
          <LoadingSpinner />
        ) : transactionsData?.items.length === 0 ? (
          <p className="text-gray-500 text-center py-8">{t('finances.noTransactions')}</p>
        ) : (
          <div className="space-y-3">
            {transactionsData?.items.map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-4 border border-gray-100 rounded-lg"
                data-testid={`transaction-row-${transaction.id}`}
              >
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg ${transaction.type === 'revenue' ? 'bg-green-100' : 'bg-red-100'}`}>
                    {transaction.type === 'revenue' ? (
                      <TrendingUp className="w-5 h-5 text-green-600" />
                    ) : transaction.employee_id ? (
                      <User className="w-5 h-5 text-red-600" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {transaction.description || (transaction.type === 'revenue' ? t('finances.typeRevenue') : t('finances.typeExpense'))}
                      {transaction.employee_name && (
                        <span className="ml-2 text-sm text-gray-500">
                          ({transaction.employee_name})
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatDate(transaction.transaction_date)} • {t(`finances.paymentMethods.${transaction.payment_method === 'bank_transfer' ? 'bankTransfer' : transaction.payment_method}`)}
                      {transaction.category_name && ` • ${transaction.category_name}`}
                      {transaction.wage_period_type && ` • ${t(`employees.wagePeriods.${transaction.wage_period_type}`)}`}
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
        title={t('finances.addTransaction')}
      >
        <TransactionForm
          leafCategories={leafCategories || []}
          onSubmit={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
        />
      </Modal>
    </div>
  )
}

function TransactionForm({
  leafCategories,
  onSubmit,
  isLoading,
}: {
  leafCategories: LeafCategory[]
  onSubmit: (data: TransactionCreate) => void
  isLoading: boolean
}) {
  const { t } = useTranslation()
  const [type, setType] = useState<TransactionType>('expense')
  const [amount, setAmount] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash')
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [description, setDescription] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])

  // Wage-specific fields
  const [employeeId, setEmployeeId] = useState<number | null>(null)
  const [wagePeriodType, setWagePeriodType] = useState<WagePeriodType>('monthly')
  const [periodStartDate, setPeriodStartDate] = useState('')
  const [periodEndDate, setPeriodEndDate] = useState('')
  const [isCalculating, setIsCalculating] = useState(false)

  // Fetch employees
  const { data: employeesData } = useQuery({
    queryKey: ['employees', { includeInactive: false }],
    queryFn: () => getEmployees(false),
  })

  const categoryOptions = leafCategories.map((cat) => ({
    id: cat.id,
    label: cat.full_path,
    searchText: cat.full_path,
  }))

  // Check if selected category is the Wages category
  const selectedCategory = leafCategories.find((cat) => cat.id === categoryId)
  const wageKeywords = ['wynagrodzenia', 'wages', 'salaries', 'salary', 'pensje', 'płace']
  const categoryTextLower = `${selectedCategory?.full_path || ''} ${selectedCategory?.name || ''}`.toLowerCase()
  const isWageCategory = wageKeywords.some(keyword => categoryTextLower.includes(keyword))

  const handleCalculateFromHours = async () => {
    if (!employeeId || !periodStartDate || !periodEndDate) {
      alert(t('employees.selectEmployeeAndPeriod'))
      return
    }

    setIsCalculating(true)
    try {
      const result = await calculateHoursForPeriod(employeeId, periodStartDate, periodEndDate)
      setAmount(result.calculated_wage.toFixed(2))
    } catch (error) {
      console.error('Failed to calculate hours:', error)
      alert(t('employees.noHoursForPeriod'))
    } finally {
      setIsCalculating(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data: TransactionCreate = {
      type,
      amount: parseFloat(amount),
      payment_method: paymentMethod,
      category_id: type === 'expense' && categoryId !== null ? categoryId : undefined,
      description: description || undefined,
      transaction_date: date,
    }

    // Add wage-specific fields if it's a wage transaction
    if (type === 'expense' && isWageCategory && employeeId) {
      data.employee_id = employeeId
      data.wage_period_type = wagePeriodType
      if (periodStartDate) data.wage_period_start = periodStartDate
      if (periodEndDate) data.wage_period_end = periodEndDate
    }

    onSubmit(data)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.status')}</label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setType('revenue')}
            className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
              type === 'revenue' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            {t('finances.typeRevenue')}
          </button>
          <button
            type="button"
            onClick={() => setType('expense')}
            className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
              type === 'expense' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            {t('finances.typeExpense')}
          </button>
        </div>
      </div>

      {type === 'expense' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t('finances.category')}</label>
          <SearchableSelect
            options={categoryOptions}
            value={categoryId}
            onChange={setCategoryId}
            placeholder={t('finances.selectCategory')}
          />
        </div>
      )}

      {/* Wage-specific fields - show when Wynagrodzenia category is selected */}
      {type === 'expense' && isWageCategory && (
        <>
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 space-y-4">
            <div className="flex items-center gap-2 text-blue-700">
              <User className="w-4 h-4" />
              <span className="font-medium">{t('employees.wageDetails')}</span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.employee')} *
              </label>
              <select
                value={employeeId || ''}
                onChange={(e) => setEmployeeId(e.target.value ? parseInt(e.target.value) : null)}
                className="input"
                required
              >
                <option value="">{t('employees.selectEmployee')}</option>
                {employeesData?.items.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name} - {employee.position_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('employees.wagePeriodType')}
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {(['daily', 'weekly', 'biweekly', 'monthly'] as WagePeriodType[]).map((period) => (
                  <button
                    key={period}
                    type="button"
                    onClick={() => setWagePeriodType(period)}
                    className={`py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                      wagePeriodType === period
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {t(`employees.wagePeriods.${period}`)}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employees.periodStart')}
                </label>
                <input
                  type="date"
                  value={periodStartDate}
                  onChange={(e) => setPeriodStartDate(e.target.value)}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('employees.periodEnd')}
                </label>
                <input
                  type="date"
                  value={periodEndDate}
                  onChange={(e) => setPeriodEndDate(e.target.value)}
                  className="input"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleCalculateFromHours}
              disabled={isCalculating || !employeeId || !periodStartDate || !periodEndDate}
              className="btn btn-secondary w-full flex items-center justify-center gap-2"
            >
              {isCalculating ? (
                <LoadingSpinner size="sm" />
              ) : (
                <Calculator className="w-4 h-4" />
              )}
              {t('employees.calculateFromHours')}
            </button>
          </div>
        </>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{t('finances.amount')}</label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="input"
          required
          data-testid="expense-amount-input"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{t('finances.paymentMethod')}</label>
        <select
          value={paymentMethod}
          onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
          className="input"
        >
          <option value="cash">{t('finances.paymentMethods.cash')}</option>
          <option value="card">{t('finances.paymentMethods.card')}</option>
          <option value="bank_transfer">{t('finances.paymentMethods.bankTransfer')}</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{t('common.date')}</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="input"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{t('finances.descriptionOptional')}</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="input"
        />
      </div>

      <button type="submit" className="btn btn-primary w-full" disabled={isLoading} data-testid="save-expense-btn">
        {isLoading ? t('common.saving') : t('common.save')}
      </button>
    </form>
  )
}
