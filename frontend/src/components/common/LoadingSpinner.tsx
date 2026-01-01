interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  /** If true, renders without wrapper padding (for inline use in buttons) */
  inline?: boolean
}

export default function LoadingSpinner({ size = 'md', inline = false }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  const spinner = (
    <div
      className={`${sizeClasses[size]} border-2 border-gray-200 border-t-primary-600 rounded-full animate-spin`}
    />
  )

  if (inline) {
    return spinner
  }

  return (
    <div className="flex items-center justify-center p-4">
      {spinner}
    </div>
  )
}
