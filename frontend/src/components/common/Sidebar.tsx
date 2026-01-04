import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  UtensilsCrossed,
  Calendar,
  Wallet,
  Package,
  FileBarChart,
  Settings,
} from 'lucide-react'

const navItems = [
  { path: '/pulpit', icon: LayoutDashboard, labelKey: 'navigation.dashboard' },
  { path: '/menu', icon: UtensilsCrossed, labelKey: 'navigation.menu' },
  { path: '/operacje', icon: Calendar, labelKey: 'navigation.dailyOperations' },
  { path: '/finanse', icon: Wallet, labelKey: 'navigation.finances' },
  { path: '/magazyn', icon: Package, labelKey: 'navigation.inventory' },
  { path: '/raporty', icon: FileBarChart, labelKey: 'navigation.reports' },
  { path: '/ustawienia', icon: Settings, labelKey: 'navigation.settings' },
]

export default function Sidebar() {
  const { t } = useTranslation()

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">{t('common.appName')}</h1>
        <p className="text-sm text-gray-500 mt-1">{t('common.appSubtitle')}</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {t(item.labelKey)}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
