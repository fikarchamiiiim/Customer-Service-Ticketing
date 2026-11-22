import { useAuth } from '../auth/AuthContext'

export function TicketsPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Tiket Saya</h1>
      <p className="text-sm text-slate-500">
        Halaman ini butuh login (<code>ProtectedRoute</code>). Daftar tiket menyusul di{' '}
        <strong>Step 3</strong>.
      </p>
      <pre className="rounded bg-slate-900 p-3 text-xs text-slate-100">
        {JSON.stringify(user, null, 2)}
      </pre>
    </div>
  )
}
