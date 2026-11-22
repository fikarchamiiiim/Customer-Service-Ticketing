import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium transition ${
    isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-200'
  }`

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-base font-semibold tracking-tight">
            CS Ticketing
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink to="/health" className={linkClass}>
              Health
            </NavLink>
            {user && (
              <>
                <NavLink to="/tickets" className={linkClass}>
                  Tiket
                </NavLink>
                {(user.role === 'agent' || user.role === 'admin') && (
                  <NavLink to="/agent" className={linkClass}>
                    Agent
                  </NavLink>
                )}
              </>
            )}
          </nav>

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <div className="text-right">
                  <p className="text-sm font-medium leading-tight">{user.name}</p>
                  <p className="text-xs text-slate-400">
                    {user.email} · <span className="font-mono">{user.role}</span>
                  </p>
                </div>
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="h-8 w-8 rounded-full"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-sm font-medium text-slate-600">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                )}
                <button
                  onClick={handleLogout}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100"
                >
                  Keluar
                </button>
              </>
            ) : (
              <NavLink to="/login" className={linkClass}>
                Login
              </NavLink>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Step 2 — auth aktif. Fitur tiket menyusul di Step 3.
      </footer>
    </div>
  )
}
