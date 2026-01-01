import client from './client'
import type { Transaction, TransactionCreate, TransactionType, PaymentMethod } from '../types'

interface TransactionFilters {
  type_filter?: TransactionType
  category_id?: number
  payment_method?: PaymentMethod
  date_from?: string
  date_to?: string
}

export async function getTransactions(filters?: TransactionFilters): Promise<{ items: Transaction[]; total: number }> {
  const { data } = await client.get('/transactions', { params: filters })
  return data
}

export async function createTransaction(transaction: TransactionCreate): Promise<Transaction> {
  const { data } = await client.post('/transactions', transaction)
  return data
}

export async function updateTransaction(id: number, updates: Partial<TransactionCreate>): Promise<Transaction> {
  const { data } = await client.put(`/transactions/${id}`, updates)
  return data
}

export async function deleteTransaction(id: number): Promise<void> {
  await client.delete(`/transactions/${id}`)
}

export async function getTransactionSummary(dateFrom: string, dateTo: string) {
  const { data } = await client.get('/transactions/summary', {
    params: { date_from: dateFrom, date_to: dateTo },
  })
  return data
}
