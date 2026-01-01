import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { DailyRecordProvider } from './context/DailyRecordContext'
import { ToastProvider } from './context/ToastContext'
import Layout from './components/common/Layout'
import DashboardPage from './pages/DashboardPage'
import MenuPage from './pages/MenuPage'
import DailyOperationsPage from './pages/DailyOperationsPage'
import FinancesPage from './pages/FinancesPage'
import InventoryPage from './pages/InventoryPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <DailyRecordProvider>
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/pulpit" replace />} />
              <Route path="/pulpit" element={<DashboardPage />} />
              <Route path="/menu" element={<MenuPage />} />
              <Route path="/operacje" element={<DailyOperationsPage />} />
              <Route path="/finanse" element={<FinancesPage />} />
              <Route path="/magazyn" element={<InventoryPage />} />
              <Route path="/raporty" element={<ReportsPage />} />
              <Route path="/ustawienia" element={<SettingsPage />} />
            </Routes>
          </Layout>
        </DailyRecordProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
