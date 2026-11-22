import { api } from './client'
import type {
  Page,
  Ticket,
  TicketListItem,
  TicketMessage,
  TicketPriority,
  TicketStatus,
} from '../types'

export type TicketFilters = {
  status?: TicketStatus | ''
  scope?: 'mine' | 'all'
  assignee?: 'me' | 'unassigned' | ''
  limit?: number
  cursor?: number | null
}

function qs(params: Record<string, string | number | null | undefined>) {
  const search = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    search.set(k, String(v))
  }
  const s = search.toString()
  return s ? `?${s}` : ''
}

export const listTickets = (f: TicketFilters) =>
  api.get<Page<TicketListItem>>(
    `/api/v1/tickets${qs({
      status: f.status,
      scope: f.scope,
      assignee: f.assignee,
      limit: f.limit ?? 20,
      cursor: f.cursor,
    })}`,
  )

export const getTicket = (id: number) => api.get<Ticket>(`/api/v1/tickets/${id}`)

export const createTicket = (data: {
  subject: string
  description: string
  priority: TicketPriority
}) => api.post<Ticket>('/api/v1/tickets', data)

export const updateTicket = (
  id: number,
  data: {
    status?: TicketStatus
    priority?: TicketPriority
    assignee_id?: number | null
  },
) => api.patch<Ticket>(`/api/v1/tickets/${id}`, data)

export const listMessages = (id: number, beforeId?: number | null, limit = 50) =>
  api.get<Page<TicketMessage>>(
    `/api/v1/tickets/${id}/messages${qs({ before_id: beforeId, limit })}`,
  )

export const createMessage = (id: number, body: string, isInternal = false) =>
  api.post<TicketMessage>(`/api/v1/tickets/${id}/messages`, {
    body,
    is_internal: isInternal,
  })
