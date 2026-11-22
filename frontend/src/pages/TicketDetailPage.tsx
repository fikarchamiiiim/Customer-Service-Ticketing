import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createMessage,
  getTicket,
  listMessages,
  updateTicket,
} from '../api/tickets'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { PriorityBadge, StatusBadge } from '../components/Badges'
import { formatTime } from '../lib/format'
import type { TicketStatus } from '../types'

/** Salinan state machine dari backend — HANYA untuk UX.
 *  Sumber kebenaran tetap server: kalau salah, server menjawab 422. */
const NEXT: Record<TicketStatus, TicketStatus[]> = {
  open: ['in_progress', 'closed'],
  in_progress: ['resolved', 'closed'],
  resolved: ['closed', 'in_progress'],
  closed: [],
}

const LABEL: Record<TicketStatus, string> = {
  open: 'Open',
  in_progress: 'In progress',
  resolved: 'Resolved',
  closed: 'Closed',
}

export function TicketDetailPage() {
  const { id } = useParams()
  const ticketId = Number(id)
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const isStaff = user?.role === 'agent' || user?.role === 'admin'

  const [body, setBody] = useState('')
  const [internal, setInternal] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const ticketQuery = useQuery({
    queryKey: ['ticket', ticketId],
    queryFn: () => getTicket(ticketId),
    enabled: Number.isFinite(ticketId),
  })

  const messagesQuery = useQuery({
    queryKey: ['ticket', ticketId, 'messages'],
    queryFn: () => listMessages(ticketId),
    enabled: Number.isFinite(ticketId),
  })

  const patch = useMutation({
    mutationFn: (data: { status?: TicketStatus; priority?: 'low' | 'normal' | 'high'; assignee_id?: number | null }) =>
      updateTicket(ticketId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] })
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      setError(null)
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Gagal mengubah tiket')
    },
  })

  const send = useMutation({
    mutationFn: () => createMessage(ticketId, body, internal),
    onSuccess: () => {
      setBody('')
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId, 'messages'] })
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] })
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      setError(null)
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Gagal mengirim pesan')
    },
  })

  if (ticketQuery.isLoading) return <p className="text-sm text-slate-500">Memuat tiket…</p>

  if (ticketQuery.isError) {
    const err = ticketQuery.error
    const is404 = err instanceof ApiError && err.status === 404
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-700">
          {is404 ? 'Tiket tidak ditemukan (atau bukan milikmu).' : (err as Error).message}
        </p>
        <Link to="/tickets" className="mt-2 inline-block text-sm underline">
          Kembali ke daftar tiket
        </Link>
      </div>
    )
  }

  const ticket = ticketQuery.data!
  const messages = messagesQuery.data?.items ?? []
  const allowed = NEXT[ticket.status]

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
      <div className="space-y-4">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-slate-400">{ticket.ticket_no}</span>
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
          </div>
          <h1 className="mt-2 text-lg font-semibold">{ticket.subject}</h1>
          <p className="mt-1 text-xs text-slate-500">
            Dibuat oleh {ticket.customer.name} ({ticket.customer.email}) ·{' '}
            {formatTime(ticket.created_at)}
          </p>
        </div>

        <div className="space-y-3">
          {messagesQuery.isLoading && <p className="text-sm text-slate-500">Memuat pesan…</p>}

          {messages.map((m) => {
            const mine = m.sender.id === user?.id
            return (
              <div
                key={m.id}
                className={`rounded-lg border p-4 ${
                  m.is_internal
                    ? 'border-amber-200 bg-amber-50'
                    : mine
                      ? 'border-slate-300 bg-slate-50'
                      : 'border-slate-200 bg-white'
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700">
                    {m.sender.name}
                    {mine && <span className="ml-1 text-slate-400">(kamu)</span>}
                    {m.is_internal && (
                      <span className="ml-2 rounded bg-amber-200 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-amber-900">
                        internal
                      </span>
                    )}
                  </span>
                  <span className="text-slate-400">{formatTime(m.created_at)}</span>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm text-slate-800">{m.body}</p>
              </div>
            )
          })}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (!body.trim()) return
            send.mutate()
          }}
          className="rounded-lg border border-slate-200 bg-white p-4"
        >
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={3}
            placeholder={
              ticket.status === 'closed' ? 'Tiket sudah ditutup' : 'Tulis balasan…'
            }
            disabled={ticket.status === 'closed'}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
          />
          <div className="mt-2 flex items-center justify-between">
            {isStaff ? (
              <label className="flex items-center gap-2 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={internal}
                  onChange={(e) => setInternal(e.target.checked)}
                />
                Catatan internal (tidak terlihat customer)
              </label>
            ) : (
              <span />
            )}
            <button
              type="submit"
              disabled={send.isPending || !body.trim() || ticket.status === 'closed'}
              className={`rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${
                internal ? 'bg-amber-600 hover:bg-amber-500' : 'bg-slate-900 hover:bg-slate-700'
              }`}
            >
              {send.isPending ? 'Mengirim…' : internal ? 'Simpan catatan' : 'Kirim'}
            </button>
          </div>
          {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        </form>
      </div>

      <aside className="space-y-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Aksi</h2>

          <div className="mt-2 flex flex-wrap gap-2">
            {allowed.length === 0 && (
              <p className="text-xs text-slate-500">Tiket sudah final.</p>
            )}
            {allowed.map((next) => {
              // customer hanya boleh menutup tiketnya sendiri
              const customerBlocked = !isStaff && next !== 'closed'
              return (
                <button
                  key={next}
                  disabled={patch.isPending || customerBlocked}
                  title={customerBlocked ? 'Hanya agent yang boleh aksi ini' : undefined}
                  onClick={() => patch.mutate({ status: next })}
                  className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  → {LABEL[next]}
                </button>
              )
            })}
          </div>

          {isStaff && (
            <>
              <hr className="my-3 border-slate-100" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Prioritas
              </h3>
              <div className="mt-2 flex gap-1">
                {(['low', 'normal', 'high'] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => patch.mutate({ priority: p })}
                    disabled={patch.isPending || ticket.priority === p}
                    className={`rounded px-2 py-1 text-xs capitalize disabled:opacity-40 ${
                      ticket.priority === p
                        ? 'bg-slate-900 text-white'
                        : 'border border-slate-300 hover:bg-slate-100'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>

              <hr className="my-3 border-slate-100" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Assignee
              </h3>
              <p className="mt-1 text-sm">
                {ticket.assignee ? ticket.assignee.name : 'Belum ditugaskan'}
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => patch.mutate({ assignee_id: user?.id ?? null })}
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                >
                  Ambil tiket
                </button>
                {ticket.assignee && (
                  <button
                    onClick={() => patch.mutate({ assignee_id: null })}
                    className="rounded-md border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                  >
                    Lepas
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs text-slate-500">
          <p>Pesan: {ticket.message_count}</p>
          <p>Update terakhir: {formatTime(ticket.updated_at)}</p>
          <p className="mt-2">
            WebSocket belum aktif — data baru terlihat setelah aksi (Step 4-5).
          </p>
        </div>
      </aside>
    </div>
  )
}
