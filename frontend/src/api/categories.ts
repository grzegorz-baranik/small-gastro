import client from './client'
import type { ExpenseCategory, LeafCategory } from '../types'

export async function getCategories(): Promise<ExpenseCategory[]> {
  const { data } = await client.get('/categories')
  return data
}

export async function getCategoryTree(): Promise<ExpenseCategory[]> {
  const { data } = await client.get('/categories/tree')
  return data
}

export async function getLeafCategories(): Promise<LeafCategory[]> {
  const { data } = await client.get('/categories/leaves')
  return data
}

export async function createCategory(category: { name: string; parent_id?: number }): Promise<ExpenseCategory> {
  const { data } = await client.post('/categories', category)
  return data
}

export async function updateCategory(id: number, updates: { name?: string; is_active?: boolean }): Promise<ExpenseCategory> {
  const { data } = await client.put(`/categories/${id}`, updates)
  return data
}

export async function deleteCategory(id: number): Promise<void> {
  await client.delete(`/categories/${id}`)
}
