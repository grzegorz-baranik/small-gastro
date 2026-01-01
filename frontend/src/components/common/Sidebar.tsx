import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  UtensilsCrossed,
  Calendar,
  Wallet,
  Package,
  Settings,
} from 'lucide-react'

const navItems = [
  { path: '/pulpit', icon: LayoutDashboard, label: 'Pulpit' },
  { path: '/menu', icon: UtensilsCrossed, label: 'Menu' },
  { path: '/operacje', icon: Calendar, label: 'Operacje dzienne' },
  { path: '/finanse', icon: Wallet, label: 'Finanse' },
  { path: '/magazyn', icon: Package, label: 'Magazyn' },
  { path: '/ustawienia', icon: Settings, label: 'Ustawienia' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">Small Gastro</h1>
        <p className="text-sm text-gray-500 mt-1">Zarzadzanie gastronomia</p>
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
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
