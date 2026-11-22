import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { HealthPage } from './pages/HealthPage'
import { LoginPage } from './pages/LoginPage'
import { AgentPage } from './pages/AgentPage'
import { TicketsPage } from './pages/TicketsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/health" replace />} />
        <Route path="/health" element={<HealthPage />} />
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/tickets"
          element={
            <ProtectedRoute>
              <TicketsPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/agent"
          element={
            <ProtectedRoute roles={['agent', 'admin']}>
              <AgentPage />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<p className="text-sm text-slate-500">404 — belum ada.</p>} />
      </Route>
    </Routes>
  )
}
