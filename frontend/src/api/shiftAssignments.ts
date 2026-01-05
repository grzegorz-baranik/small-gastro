import client from './client'
import type { ShiftAssignment, ShiftAssignmentCreate, ShiftAssignmentUpdate } from '../types'

export interface ShiftAssignmentsListResponse {
  items: ShiftAssignment[]
  total: number
}

export async function getShiftAssignments(dailyRecordId: number): Promise<ShiftAssignmentsListResponse> {
  const { data } = await client.get(`/daily-records/${dailyRecordId}/shifts`)
  return data
}

export async function createShiftAssignment(
  dailyRecordId: number,
  assignment: ShiftAssignmentCreate
): Promise<ShiftAssignment> {
  const { data } = await client.post(`/daily-records/${dailyRecordId}/shifts`, assignment)
  return data
}

export async function updateShiftAssignment(
  dailyRecordId: number,
  shiftId: number,
  updates: ShiftAssignmentUpdate
): Promise<ShiftAssignment> {
  const { data } = await client.put(`/daily-records/${dailyRecordId}/shifts/${shiftId}`, updates)
  return data
}

export async function deleteShiftAssignment(dailyRecordId: number, shiftId: number): Promise<void> {
  await client.delete(`/daily-records/${dailyRecordId}/shifts/${shiftId}`)
}
