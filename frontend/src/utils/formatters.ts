export function formatCurrency(amount: number | string): string {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('pl-PL', {
    style: 'currency',
    currency: 'PLN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numAmount)
}

export function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(dateString))
}

export function formatDateTime(dateString: string): string {
  return new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(dateString))
}

/**
 * Infer unit type from unit label.
 * Weight-based units: 'kg', 'g'
 * Count-based units: everything else (szt, opak, etc.)
 */
export function inferUnitType(unitLabel: string): 'weight' | 'count' {
  const weightUnits = ['kg', 'g', 'gram', 'grams', 'kilogram', 'kilograms']
  return weightUnits.includes(unitLabel.toLowerCase()) ? 'weight' : 'count'
}

/**
 * Check if a unit label represents grams (needs conversion to kg)
 */
function isGramUnit(unitLabel: string): boolean {
  return ['g', 'gram', 'grams'].includes(unitLabel.toLowerCase())
}

/**
 * Format a quantity with its unit.
 *
 * For weight-based ingredients:
 * - Always displays in kg
 * - If stored in grams (unit_label='g'), converts to kg
 *
 * For count-based ingredients:
 * - Displays as whole numbers with their unit label
 *
 * @param value - The quantity value
 * @param unitType - 'weight' or 'count'
 * @param unitLabel - The ingredient's unit label (e.g., 'kg', 'g', 'szt')
 */
export function formatQuantity(
  value: number | string,
  unitType: string,
  unitLabel?: string
): string {
  let numValue = typeof value === 'string' ? parseFloat(value) : value

  if (unitType === 'weight') {
    // Convert grams to kg if needed
    if (unitLabel && isGramUnit(unitLabel)) {
      numValue = numValue / 1000
    }
    // Always display weight in kg with 2 decimal places
    return `${numValue.toFixed(2)} kg`
  }

  // Count-based: show whole numbers with unit label
  const displayLabel = unitLabel || 'szt.'
  return `${Math.round(numValue)} ${displayLabel}`
}

export function formatPercent(value: number | string, decimals: number = 1): string {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  return `${numValue.toFixed(decimals)}%`
}

export function getTodayDateString(): string {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

export function getDateString(date: Date): string {
  return date.toISOString().split('T')[0]
}

export function getDateDaysAgo(days: number): string {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return getDateString(date)
}
