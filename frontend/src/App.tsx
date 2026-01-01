import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { DailyRecordProvider } from './context/DailyRecordContext'
import Layout from './components/common/Layout'
import DashboardPage from './pages/DashboardPage'
import MenuPage from './pages/MenuPage'
import DailyOperationsPage from './pages/DailyOperationsPage'
import FinancesPage from './pages/FinancesPage'
import InventoryPage from './pages/InventoryPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <DailyRecordProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/pulpit" replace />} />
            <Route path="/pulpit" element={<DashboardPage />} />
            <Route path="/menu" element={<MenuPage />} />
            <Route path="/operacje" element={<DailyOperationsPage />} />
            <Route path="/finanse" element={<FinancesPage />} />
            <Route path="/magazyn" element={<InventoryPage />} />
            <Route path="/ustawienia" element={<SettingsPage />} />
          </Routes>
        </Layout>
      </DailyRecordProvider>
    </BrowserRouter>
  )
}

export default App
