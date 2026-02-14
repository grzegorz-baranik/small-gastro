import client from './client'
import type {
  Delivery,
  DeliveryCreate,
  StorageTransfer,
  StorageTransferCreate,
  Spoilage,
  SpoilageCreate,
  TransferStockItem,
} from '../types'

// Deliveries API

/**
 * Create a new delivery record
 */
export async function createDelivery(delivery: DeliveryCreate): Promise<Delivery> {
  const { data } = await client.post<Delivery>('/deliveries', delivery)
  return data
}

/**
 * Get deliveries for a specific daily record
 */
export async function getDeliveries(dailyRecordId: number): Promise<Delivery[]> {
  const { data } = await client.get<{ items: Delivery[]; total: number }>('/deliveries', {
    params: { daily_record_id: dailyRecordId },
  })
  return data.items
}

/**
 * Delete a delivery record
 */
export async function deleteDelivery(id: number): Promise<void> {
  await client.delete(`/deliveries/${id}`)
}

// Storage Transfers API

/**
 * Create a new storage transfer record
 */
export async function createTransfer(transfer: StorageTransferCreate): Promise<StorageTransfer> {
  const { data } = await client.post<StorageTransfer>('/transfers', transfer)
  return data
}

/**
 * Get transfers for a specific daily record
 */
export async function getTransfers(dailyRecordId: number): Promise<StorageTransfer[]> {
  const { data } = await client.get<{ items: StorageTransfer[]; total: number }>('/transfers', {
    params: { daily_record_id: dailyRecordId },
  })
  return data.items
}

/**
 * Delete a transfer record
 */
export async function deleteTransfer(id: number): Promise<void> {
  await client.delete(`/transfers/${id}`)
}

// Spoilage API

/**
 * Create a new spoilage record
 */
export async function createSpoilage(spoilage: SpoilageCreate): Promise<Spoilage> {
  const { data } = await client.post<Spoilage>('/spoilage', spoilage)
  return data
}

/**
 * Get spoilage records for a specific daily record
 */
export async function getSpoilage(dailyRecordId: number): Promise<Spoilage[]> {
  const { data } = await client.get<{ items: Spoilage[]; total: number }>('/spoilage', {
    params: { daily_record_id: dailyRecordId },
  })
  return data.items
}

/**
 * Delete a spoilage record
 */
export async function deleteSpoilage(id: number): Promise<void> {
  await client.delete(`/spoilage/${id}`)
}

// Transfer Stock Info API

/**
 * Get stock information for transfer modal (storage and shop quantities)
 */
export async function getTransferStockInfo(dailyRecordId: number): Promise<TransferStockItem[]> {
  const { data } = await client.get<TransferStockItem[]>(`/inventory/daily-record/${dailyRecordId}/transfer-stock`)
  return data
}
