import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { UserRole } from '../types'

type Props = {
  children: React.ReactNode
  roles?: UserRole[]
}

export function ProtectedRoute({ children, roles }: Props) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  // Selama sesi masih dicek, JANGAN redirect — kalau tidak, user yang sah
  // akan sempat terlempar ke /login setiap kali halaman di-refresh.
  if (isLoading) {
    return <p className="text-sm text-slate-500">Memeriksa sesi…</p>
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (roles && !roles.includes(user.role)) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
        <h2 className="font-medium text-amber-900">Akses ditolak</h2>
        <p className="mt-1 text-sm text-amber-800">
          Halaman ini hanya untuk role: <strong>{roles.join(', ')}</strong>. Role kamu:{' '}
          <strong>{user.role}</strong>.
        </p>
      </div>
    )
  }

  return <>{children}</>
}

export function homeFor(role: UserRole | undefined): string {
  return role === 'agent' || role === 'admin' ? '/agent' : '/tickets'
}
