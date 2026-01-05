import client from './client'
import type { Employee, EmployeeCreate, EmployeeUpdate } from '../types'

export interface EmployeesListResponse {
  items: Employee[]
  total: number
}

export async function getEmployees(includeInactive: boolean = false): Promise<EmployeesListResponse> {
  const { data } = await client.get('/employees', {
    params: { include_inactive: includeInactive }
  })
  return data
}

export async function getEmployee(id: number): Promise<Employee> {
  const { data } = await client.get(`/employees/${id}`)
  return data
}

export async function createEmployee(employee: EmployeeCreate): Promise<Employee> {
  const { data } = await client.post('/employees', employee)
  return data
}

export async function updateEmployee(id: number, updates: EmployeeUpdate): Promise<Employee> {
  const { data } = await client.put(`/employees/${id}`, updates)
  return data
}

export async function deactivateEmployee(id: number): Promise<Employee> {
  const { data } = await client.patch(`/employees/${id}/deactivate`)
  return data
}

export async function activateEmployee(id: number): Promise<Employee> {
  const { data } = await client.patch(`/employees/${id}/activate`)
  return data
}
