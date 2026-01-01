import { useEffect, useRef } from 'react'
import { AlertTriangle, X } from 'lucide-react'

interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'default'
  isLoading?: boolean
}

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Potwierdz',
  cancelText = 'Anuluj',
  variant = 'default',
  isLoading = false,
}: ConfirmDialogProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const cancelButtonRef = useRef<HTMLButtonElement>(null)

  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  // Focus cancel button when dialog opens (safer default)
  useEffect(() => {
    if (isOpen && cancelButtonRef.current) {
      cancelButtonRef.current.focus()
    }
  }, [isOpen])

  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  const variantStyles = {
    danger: {
      icon: 'bg-red-100 text-red-600',
      button: 'btn-danger',
    },
    warning: {
      icon: 'bg-yellow-100 text-yellow-600',
      button: 'bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500',
    },
    default: {
      icon: 'bg-blue-100 text-blue-600',
      button: 'btn-primary',
    },
  }

  const styles = variantStyles[variant]

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="fixed inset-0 bg-black/50 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
        <div
          className="relative bg-white rounded-xl shadow-xl w-full max-w-md transform transition-all"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="confirm-dialog-title"
          aria-describedby="confirm-dialog-description"
        >
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-full ${styles.icon}`}>
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3
                  id="confirm-dialog-title"
                  className="text-lg font-semibold text-gray-900"
                >
                  {title}
                </h3>
                <p
                  id="confirm-dialog-description"
                  className="mt-2 text-sm text-gray-600"
                >
                  {message}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Zamknij"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="mt-6 flex gap-3 justify-end">
              <button
                ref={cancelButtonRef}
                onClick={onClose}
                className="btn btn-secondary"
                disabled={isLoading}
              >
                {cancelText}
              </button>
              <button
                ref={confirmButtonRef}
                onClick={onConfirm}
                className={`btn ${styles.button}`}
                disabled={isLoading}
              >
                {isLoading ? 'Przetwarzanie...' : confirmText}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
