// Shift Assignment types

export interface ShiftAssignment {
  id: number
  employee_id: number
  employee_name: string
  start_time: string  // "HH:MM" format
  end_time: string    // "HH:MM" format
  hours_worked: number
  hourly_rate: number
}

export interface ShiftAssignmentCreate {
  employee_id: number
  start_time: string  // "HH:MM" format
  end_time: string    // "HH:MM" format
}

export interface ShiftAssignmentUpdate {
  start_time: string  // "HH:MM" format
  end_time: string    // "HH:MM" format
}
