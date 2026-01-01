import client from './client'
import type { Ingredient, IngredientCreate } from '../types'

export async function getIngredients(): Promise<{ items: Ingredient[]; total: number }> {
  const { data } = await client.get('/ingredients/')
  return data
}

export async function createIngredient(ingredient: IngredientCreate): Promise<Ingredient> {
  const { data } = await client.post('/ingredients/', ingredient)
  return data
}

export async function updateIngredient(id: number, updates: Partial<IngredientCreate>): Promise<Ingredient> {
  const { data } = await client.put(`/ingredients/${id}`, updates)
  return data
}

export async function deleteIngredient(id: number): Promise<void> {
  await client.delete(`/ingredients/${id}`)
}
