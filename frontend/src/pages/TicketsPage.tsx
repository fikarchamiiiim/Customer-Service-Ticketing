import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listTickets, type TicketFilters } from '../api/tickets'
import { useAuth } from '../auth/AuthContext'
import { PriorityBadge, StatusBadge } from '../components/Badges'
import { relativeTime } from '../lib/format'
import type { TicketStatus } from '../types'

const STATUS_OPTIONS: { value: TicketStatus | ''; label: string }[] = [
  { value: '', label: 'Semua status' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
]

export function TicketsPage() {
  const { user } = useAuth()
  const isStaff = user?.role === 'agent' || user?.role === 'admin'

  // Agent default: lihat SEMUA tiket. Customer: hanya miliknya (dipaksa server juga).
  const [filters, setFilters] = useState<TicketFilters>({
    status: '',
    scope: isStaff ? 'all' : 'mine',
    assignee: '',
  })

  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: ['tickets', filters],
    queryFn: () => listTickets(filters),
  })

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Tiket</h1>
          <p className="text-sm text-slate-500">
            {isStaff ? 'Semua tiket dari seluruh customer.' : 'Tiket yang kamu buat.'}
          </p>
        </div>
        <Link
          to="/tickets/new"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          + Tiket baru
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white p-3">
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value as TicketStatus | '' }))}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        {isStaff && (
          <>
            <select
              value={filters.scope}
              onChange={(e) =>
                setFilters((f) => ({ ...f, scope: e.target.value as 'mine' | 'all' }))
              }
              className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            >
              <option value="all">Semua tiket</option>
              <option value="mine">Tiket saya</option>
            </select>

            <select
              value={filters.assignee}
              onChange={(e) =>
                setFilters((f) => ({
                  ...f,
                  assignee: e.target.value as 'me' | 'unassigned' | '',
                }))
              }
              className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            >
              <option value="">Semua assignee</option>
              <option value="me">Ditugaskan ke saya</option>
              <option value="unassigned">Belum diambil</option>
            </select>
          </>
        )}

        {isFetching && <span className="text-xs text-slate-400">memuat…</span>}
      </div>

      {isLoading && <p className="text-sm text-slate-500">Memuat tiket…</p>}

      {isError && (
        <p className="rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error instanceof Error ? error.message : 'Gagal memuat tiket'}
        </p>
      )}

      {data && data.items.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center">
          <p className="text-sm text-slate-500">Belum ada tiket.</p>
          <Link to="/tickets/new" className="mt-2 inline-block text-sm font-medium text-slate-900 underline">
            Buat tiket pertama
          </Link>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">No</th>
                <th className="px-4 py-2 font-medium">Subjek</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Prioritas</th>
                <th className="px-4 py-2 font-medium">Assignee</th>
                <th className="px-4 py-2 font-medium">Aktivitas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((t) => (
                <tr key={t.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-500">
                    <Link to={`/tickets/${t.id}`} className="hover:underline">
                      {t.ticket_no}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/tickets/${t.id}`} className="font-medium hover:underline">
                      {t.subject}
                    </Link>
                    <p className="text-xs text-slate-400">{t.customer.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={t.status} />
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={t.priority} />
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {t.assignee ? t.assignee.name : <span className="text-slate-400">—</span>}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-500">
                    {relativeTime(t.last_message_at ?? t.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
