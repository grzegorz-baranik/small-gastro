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

export function formatWeight(grams: number | string): string {
  const numGrams = typeof grams === 'string' ? parseFloat(grams) : grams
  if (numGrams >= 1000) {
    return `${(numGrams / 1000).toFixed(2)} kg`
  }
  return `${numGrams.toFixed(0)} g`
}

export function formatQuantity(value: number | string, unitType: string): string {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (unitType === 'weight') {
    return formatWeight(numValue)
  }
  return `${numValue} szt.`
}

export function getTodayDateString(): string {
  const today = new Date()
  return today.toISOString().split('T')[0]
}
