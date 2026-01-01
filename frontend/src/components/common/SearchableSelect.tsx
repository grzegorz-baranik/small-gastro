import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Search, X } from 'lucide-react'

export interface SelectOption {
  id: number
  label: string
  searchText: string
}

interface SearchableSelectProps {
  options: SelectOption[]
  value: number | null
  onChange: (value: number | null) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = 'Wybierz...',
  disabled = false,
  className = '',
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selectedOption = options.find((opt) => opt.id === value)

  const filteredOptions = options.filter((opt) =>
    opt.searchText.toLowerCase().includes(search.toLowerCase())
  )

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    setHighlightedIndex(0)
  }, [search])

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault()
        setIsOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((prev) => Math.min(prev + 1, filteredOptions.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((prev) => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (filteredOptions[highlightedIndex]) {
          onChange(filteredOptions[highlightedIndex].id)
          setIsOpen(false)
          setSearch('')
        }
        break
      case 'Escape':
        setIsOpen(false)
        setSearch('')
        break
    }
  }

  function handleSelect(optionId: number) {
    onChange(optionId)
    setIsOpen(false)
    setSearch('')
  }

  function handleClear(e: React.MouseEvent) {
    e.stopPropagation()
    onChange(null)
    setSearch('')
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={`
          w-full flex items-center justify-between px-3 py-2
          border border-gray-300 rounded-lg bg-white text-left
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'hover:border-gray-400 cursor-pointer'}
        `}
      >
        <span className={selectedOption ? 'text-gray-900' : 'text-gray-500'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <div className="flex items-center gap-1">
          {value !== null && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-0.5 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg">
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Szukaj..."
                className="w-full pl-8 pr-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
          <ul className="max-h-60 overflow-y-auto py-1">
            {filteredOptions.length === 0 ? (
              <li className="px-3 py-2 text-gray-500 text-sm">Brak wynikow</li>
            ) : (
              filteredOptions.map((option, index) => (
                <li
                  key={option.id}
                  onClick={() => handleSelect(option.id)}
                  className={`
                    px-3 py-2 cursor-pointer text-sm
                    ${index === highlightedIndex ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'}
                    ${option.id === value ? 'font-medium' : ''}
                  `}
                >
                  {option.label}
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
