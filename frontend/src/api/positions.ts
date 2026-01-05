import client from './client'
import type { Position, PositionCreate, PositionUpdate } from '../types'

export interface PositionsListResponse {
  items: Position[]
  total: number
}

export async function getPositions(): Promise<PositionsListResponse> {
  const { data } = await client.get('/positions')
  return data
}

export async function getPosition(id: number): Promise<Position> {
  const { data } = await client.get(`/positions/${id}`)
  return data
}

export async function createPosition(position: PositionCreate): Promise<Position> {
  const { data } = await client.post('/positions', position)
  return data
}

export async function updatePosition(id: number, updates: PositionUpdate): Promise<Position> {
  const { data } = await client.put(`/positions/${id}`, updates)
  return data
}

export async function deletePosition(id: number): Promise<void> {
  await client.delete(`/positions/${id}`)
}
