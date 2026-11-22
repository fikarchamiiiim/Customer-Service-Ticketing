import { useAuth } from '../auth/AuthContext'

export function AgentPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Area Agent</h1>
      <p className="text-sm text-slate-500">
        Halaman ini dijaga <code>ProtectedRoute roles={['agent','admin']}</code>. Hanya role
        agent/admin yang bisa membukanya.
      </p>
      <pre className="rounded bg-slate-900 p-3 text-xs text-slate-100">
        {JSON.stringify(user, null, 2)}
      </pre>
      <p className="text-sm text-slate-500">
        Queue tiket akan dibangun di <strong>Step 3</strong>.
      </p>
    </div>
  )
}
