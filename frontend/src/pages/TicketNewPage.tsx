import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createTicket } from '../api/tickets'
import { ApiError } from '../api/client'
import type { TicketPriority } from '../types'

export function TicketNewPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<TicketPriority>('normal')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => createTicket({ subject, description, priority }),
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      navigate(`/tickets/${ticket.id}`, { replace: true })
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Gagal membuat tiket')
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        setError(null)
        mutation.mutate()
      }}
      className="mx-auto max-w-2xl space-y-4"
    >
      <div>
        <h1 className="text-xl font-semibold">Tiket baru</h1>
        <p className="text-sm text-slate-500">
          Jelaskan masalahmu. Deskripsi ini otomatis menjadi pesan pertama.
        </p>
      </div>

      <label className="block">
        <span className="text-sm font-medium">Subjek</span>
        <input
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          required
          minLength={3}
          maxLength={200}
          placeholder="Ringkas masalahnya (3-200 karakter)"
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium">Deskripsi</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={7}
          maxLength={5000}
          placeholder="Ceritakan detail: apa yang terjadi, sejak kapan, apa yang sudah dicoba…"
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <span className="text-xs text-slate-400">{description.length}/5000</span>
      </label>

      <label className="block">
        <span className="text-sm font-medium">Prioritas</span>
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as TicketPriority)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
        </select>
      </label>

      {error && (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {mutation.isPending ? 'Mengirim…' : 'Buat tiket'}
        </button>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
        >
          Batal
        </button>
      </div>
    </form>
  )
}
