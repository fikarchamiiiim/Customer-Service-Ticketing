import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HealthPage } from './pages/HealthPage'
import { LoginPage } from './pages/LoginPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/health" replace />} />
        <Route path="/health" element={<HealthPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<p className="text-sm text-slate-500">404 — belum ada.</p>} />
      </Route>
    </Routes>
  )
}
