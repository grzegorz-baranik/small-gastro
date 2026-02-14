import { ReactNode, useEffect, useRef, useCallback } from 'react'
import { X } from 'lucide-react'

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: ReactNode
  size?: ModalSize
  /** If true, prevents closing on Escape key or backdrop click */
  preventClose?: boolean
}

const sizeClasses: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '3xl': 'max-w-3xl',
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'lg',
  preventClose = false,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)
  const previousActiveElement = useRef<Element | null>(null)

  // Handle Escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !preventClose) {
        onClose()
      }
    },
    [onClose, preventClose]
  )

  // Handle backdrop click
  const handleBackdropClick = () => {
    if (!preventClose) {
      onClose()
    }
  }

  // Manage focus trap and body scroll
  useEffect(() => {
    if (isOpen) {
      // Store the previously focused element
      previousActiveElement.current = document.activeElement

      // Disable body scroll
      document.body.style.overflow = 'hidden'

      // Add keyboard listener
      document.addEventListener('keydown', handleKeyDown)

      // Focus the modal container
      if (modalRef.current) {
        // Focus first focusable element or the close button
        const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        if (focusableElements.length > 0) {
          // Focus the first input if available, otherwise first focusable element
          const firstInput = modalRef.current.querySelector<HTMLElement>(
            'input:not([type="hidden"]), select, textarea'
          )
          if (firstInput) {
            setTimeout(() => firstInput.focus(), 50)
          } else {
            setTimeout(() => focusableElements[0].focus(), 50)
          }
        }
      }
    }

    return () => {
      document.body.style.overflow = 'unset'
      document.removeEventListener('keydown', handleKeyDown)

      // Restore focus to previously focused element
      if (previousActiveElement.current instanceof HTMLElement) {
        previousActiveElement.current.focus()
      }
    }
  }, [isOpen, handleKeyDown])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="fixed inset-0 bg-black/50 transition-opacity"
          onClick={handleBackdropClick}
          aria-hidden="true"
        />
        <div
          ref={modalRef}
          className={`relative bg-white rounded-xl shadow-xl w-full animate-scale-in ${sizeClasses[size]}`}
        >
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 id="modal-title" className="text-lg font-semibold text-gray-900">
              {title}
            </h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Zamknij"
              disabled={preventClose}
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
          <div className="p-6">{children}</div>
        </div>
      </div>
    </div>
  )
}
