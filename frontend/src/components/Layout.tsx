import { Link, NavLink, Outlet } from 'react-router-dom'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium transition ${
    isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-200'
  }`

export function Layout() {
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
            <NavLink to="/login" className={linkClass}>
              Login
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Step 0 — scaffolding. Belum ada auth &amp; tiket.
      </footer>
    </div>
  )
}
