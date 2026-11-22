import type { TicketPriority, TicketStatus } from '../types'

const STATUS_STYLE: Record<TicketStatus, string> = {
  open: 'bg-blue-100 text-blue-800 ring-blue-200',
  in_progress: 'bg-amber-100 text-amber-800 ring-amber-200',
  resolved: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  closed: 'bg-slate-200 text-slate-600 ring-slate-300',
}

const STATUS_LABEL: Record<TicketStatus, string> = {
  open: 'Open',
  in_progress: 'In progress',
  resolved: 'Resolved',
  closed: 'Closed',
}

const PRIORITY_STYLE: Record<TicketPriority, string> = {
  low: 'bg-slate-100 text-slate-600 ring-slate-200',
  normal: 'bg-sky-50 text-sky-700 ring-sky-200',
  high: 'bg-rose-100 text-rose-700 ring-rose-200',
}

export function StatusBadge({ status }: { status: TicketStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${STATUS_STYLE[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${PRIORITY_STYLE[priority]}`}
    >
      {priority}
    </span>
  )
}
