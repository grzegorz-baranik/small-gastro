// Wage Analytics types

export interface WageSummary {
  total_wages: number
  total_hours: number
  avg_cost_per_hour: number
}

export interface EmployeeWageStats {
  employee_id: number
  employee_name: string
  position_name: string
  hours_worked: number
  wages_paid: number
  cost_per_hour: number
  previous_month_wages: number | null
  change_percent: number | null
}

export interface WageAnalyticsResponse {
  summary: WageSummary
  previous_month_summary: WageSummary | null
  by_employee: EmployeeWageStats[]
}

export interface HoursCalculationResponse {
  employee_id: number
  hours: number
  calculated_wage: number
}
