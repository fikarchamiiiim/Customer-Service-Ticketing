import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchDevConfig } from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import { homeFor } from '../auth/ProtectedRoute'
import { ApiError } from '../api/client'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (r: { credential: string }) => void }) => void
          renderButton: (el: HTMLElement, options: Record<string, unknown>) => void
        }
      }
    }
  }
}

const DEV_ACCOUNTS = [
  { email: 'agent1@example.com', label: 'Agent Satu', role: 'agent' },
  { email: 'agent2@example.com', label: 'Agent Dua', role: 'agent' },
  { email: 'customer1@example.com', label: 'Budi (customer)', role: 'customer' },
  { email: 'customer2@example.com', label: 'Siti (customer)', role: 'customer' },
]

export function LoginPage() {
  const { user, loginGoogle, loginAsDev } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const { data: config } = useQuery({
    queryKey: ['dev-config'],
    queryFn: fetchDevConfig,
    staleTime: Infinity,
  })

  const from = (location.state as { from?: string } | null)?.from

  // Sudah login? langsung ke halaman sesuai role.
  useEffect(() => {
    if (user) navigate(from ?? homeFor(user.role), { replace: true })
  }, [user, from, navigate])

  // Muat skrip Google Identity Services, LALU inisialisasi.
  // Dulu dipisah dua effect: efek init bisa jalan sebelum skrip selesai dimuat,
  // window.google masih undefined, dan tombol tidak pernah muncul.
  useEffect(() => {
    if (!config?.google_enabled) return

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined
    if (!clientId) {
      setError('VITE_GOOGLE_CLIENT_ID belum diisi di frontend/.env.local — restart (make fe)')
      return
    }

    let cancelled = false

    function initGoogle() {
      if (cancelled || !window.google) return
      window.google.accounts.id.initialize({
        client_id: clientId!,
        callback: async ({ credential }) => {
          setBusy(true)
          setError(null)
          try {
            const u = await loginGoogle(credential)
            navigate(from ?? homeFor(u.role), { replace: true })
          } catch (err) {
            setError(err instanceof ApiError ? err.message : 'Login Google gagal')
          } finally {
            setBusy(false)
          }
        },
      })
      const el = document.getElementById('gsi-button')
      if (el) {
        window.google.accounts.id.renderButton(el, {
          theme: 'outline',
          size: 'large',
          width: 320,
        })
      }
    }

    if (window.google) {
      initGoogle()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = initGoogle
    script.onerror = () => setError('Gagal memuat skrip Google. Cek koneksi / AdBlock.')
    document.head.appendChild(script)

    return () => {
      cancelled = true
      script.remove()
    }
  }, [config?.google_enabled, loginGoogle, navigate, from])

  async function handleDevLogin(email: string) {
    setBusy(true)
    setError(null)
    try {
      const u = await loginAsDev(email)
      navigate(from ?? homeFor(u.role), { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login gagal')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold">Masuk</h1>
        <p className="mt-1 text-sm text-slate-500">
          Gunakan akun Google, atau panel dev di bawah kalau Google belum dikonfigurasi.
        </p>

        {config?.google_enabled ? (
          <div id="gsi-button" className="mt-5" />
        ) : (
          <p className="mt-5 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
            <code className="font-medium">GOOGLE_CLIENT_ID</code> belum diisi di{' '}
            <code>.env</code> — tombol Google dinonaktifkan. Ikuti checklist di{' '}
            <code>docs/GOOGLE-SETUP.md</code> lalu restart backend.
          </p>
        )}

        {error && (
          <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
        )}
      </div>

      {config?.dev_auth && (
        <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50/60 p-5">
          <h2 className="text-sm font-semibold text-amber-900">Dev login (DEV_AUTH=true)</h2>
          <p className="mt-1 text-xs text-amber-800">
            Tanpa Google. Pilih salah satu akun seed — role diambil dari allowlist server,
            bukan dari pilihan ini.
          </p>
          <div className="mt-3 grid gap-2">
            {DEV_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                disabled={busy}
                onClick={() => handleDevLogin(acc.email)}
                className="flex items-center justify-between rounded-md border border-amber-200 bg-white px-3 py-2 text-left text-sm hover:bg-amber-100 disabled:opacity-50"
              >
                <span>
                  <span className="font-medium">{acc.label}</span>
                  <span className="ml-2 text-xs text-slate-400">{acc.email}</span>
                </span>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  {acc.role}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
