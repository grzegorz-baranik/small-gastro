import client from './client'
import type { Product, ProductCreate } from '../types'

export async function getProducts(activeOnly = true): Promise<{ items: Product[]; total: number }> {
  const { data } = await client.get('/products/', { params: { active_only: activeOnly } })
  return data
}

export async function createProduct(product: ProductCreate): Promise<Product> {
  const { data } = await client.post('/products/', product)
  return data
}

export async function updateProduct(id: number, updates: Partial<ProductCreate>): Promise<Product> {
  const { data } = await client.put(`/products/${id}`, updates)
  return data
}

export async function deleteProduct(id: number): Promise<void> {
  await client.delete(`/products/${id}`)
}

export async function addProductIngredient(productId: number, ingredientId: number, quantity: number) {
  const { data } = await client.post(`/products/${productId}/ingredients`, {
    ingredient_id: ingredientId,
    quantity,
  })
  return data
}

export async function updateProductIngredient(productId: number, ingredientId: number, quantity: number) {
  const { data } = await client.put(`/products/${productId}/ingredients/${ingredientId}`, { quantity })
  return data
}

export async function removeProductIngredient(productId: number, ingredientId: number): Promise<void> {
  await client.delete(`/products/${productId}/ingredients/${ingredientId}`)
}
