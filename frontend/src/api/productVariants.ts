import client from './client'
import type {
  ProductVariant,
  ProductVariantCreate,
  ProductVariantUpdate,
  ProductVariantListResponse,
  ProductVariantWithIngredients,
  VariantIngredient,
  VariantIngredientCreate,
  VariantIngredientUpdate,
  VariantIngredientListResponse,
} from '../types'

// Product Variant CRUD operations

export async function getVariants(productId: number, activeOnly = true): Promise<ProductVariantListResponse> {
  const { data } = await client.get(`/products/${productId}/variants`, {
    params: { active_only: activeOnly },
  })
  return data
}

export async function getVariant(productId: number, variantId: number): Promise<ProductVariantWithIngredients> {
  const { data } = await client.get(`/products/${productId}/variants/${variantId}`)
  return data
}

export async function createVariant(productId: number, variant: ProductVariantCreate): Promise<ProductVariant> {
  const { data } = await client.post(`/products/${productId}/variants`, variant)
  return data
}

export async function updateVariant(
  productId: number,
  variantId: number,
  updates: ProductVariantUpdate
): Promise<ProductVariant> {
  const { data } = await client.put(`/products/${productId}/variants/${variantId}`, updates)
  return data
}

export async function deleteVariant(productId: number, variantId: number): Promise<void> {
  await client.delete(`/products/${productId}/variants/${variantId}`)
}

// Variant Ingredient (Recipe) operations

export async function getVariantIngredients(variantId: number): Promise<VariantIngredientListResponse> {
  const { data } = await client.get(`/products/variants/${variantId}/ingredients`)
  return data
}

export async function addVariantIngredient(
  variantId: number,
  ingredient: VariantIngredientCreate
): Promise<VariantIngredient> {
  const { data } = await client.post(`/products/variants/${variantId}/ingredients`, ingredient)
  return data
}

export async function updateVariantIngredient(
  variantId: number,
  ingredientId: number,
  updates: VariantIngredientUpdate
): Promise<VariantIngredient> {
  const { data } = await client.put(`/products/variants/${variantId}/ingredients/${ingredientId}`, updates)
  return data
}

export async function removeVariantIngredient(variantId: number, ingredientId: number): Promise<void> {
  await client.delete(`/products/variants/${variantId}/ingredients/${ingredientId}`)
}
