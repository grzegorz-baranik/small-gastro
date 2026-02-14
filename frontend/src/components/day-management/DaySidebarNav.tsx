import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  FileText,
  Play,
  Users,
  Package,
  ShoppingCart,
  Square,
  ArrowLeft,
} from 'lucide-react'

type DaySection = 'overview' | 'opening' | 'shifts' | 'operations' | 'sales' | 'closing'

interface DaySidebarNavProps {
  currentSection: DaySection
  onSectionChange: (section: DaySection) => void
  dayStatus: 'open' | 'closed'
  dayDate: string
}

interface NavItem {
  id: DaySection
  labelKey: string
  icon: typeof FileText
}

const navItems: NavItem[] = [
  { id: 'overview', labelKey: 'dayManagement.sections.overview', icon: FileText },
  { id: 'opening', labelKey: 'dayManagement.sections.opening', icon: Play },
  { id: 'shifts', labelKey: 'dayManagement.sections.shifts', icon: Users },
  { id: 'operations', labelKey: 'dayManagement.sections.operations', icon: Package },
  { id: 'sales', labelKey: 'dayManagement.sections.sales', icon: ShoppingCart },
  { id: 'closing', labelKey: 'dayManagement.sections.closing', icon: Square },
]

export default function DaySidebarNav({
  currentSection,
  onSectionChange,
  dayStatus,
  dayDate,
}: DaySidebarNavProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('pl-PL', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  }

  const handleBackToList = () => {
    navigate('/operacje')
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Day header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 capitalize">
          {formatDate(dayDate)}
        </h2>
        <div className="mt-2">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              dayStatus === 'open'
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {dayStatus === 'open'
              ? t('dailyOperations.statusOpen')
              : t('dailyOperations.statusClosed')}
          </span>
        </div>
      </div>

      {/* Navigation items */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentSection === item.id

          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left ${
                isActive
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span>{t(item.labelKey)}</span>
            </button>
          )
        })}
      </nav>

      {/* Back to list link */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={handleBackToList}
          className="w-full flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t('dayManagement.backToList')}</span>
        </button>
      </div>
    </aside>
  )
}

export type { DaySection, DaySidebarNavProps }
