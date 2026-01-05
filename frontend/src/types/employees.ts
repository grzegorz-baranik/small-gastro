// Employee types

export interface Employee {
  id: number
  name: string
  position_id: number
  position_name: string
  hourly_rate: number  // Effective rate (override or position default)
  is_active: boolean
  created_at: string
}

export interface EmployeeCreate {
  name: string
  position_id: number
  hourly_rate?: number | null  // If null, use position's default rate
  is_active?: boolean
}

export interface EmployeeUpdate {
  name?: string
  position_id?: number
  hourly_rate?: number | null
}
