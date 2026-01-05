// Position types

export interface Position {
  id: number
  name: string
  hourly_rate: number
  employee_count: number
  created_at: string
}

export interface PositionCreate {
  name: string
  hourly_rate: number
}

export interface PositionUpdate {
  name?: string
  hourly_rate?: number
}
