export type UserRole = 'customer' | 'agent' | 'admin'

export type User = {
  id: number
  email: string
  name: string
  avatar_url: string | null
  role: UserRole
}

export type DevConfig = {
  dev_auth: boolean
  google_enabled: boolean
  session_cookie: string
}

export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed'
export type TicketPriority = 'low' | 'normal' | 'high'

export type TicketListItem = {
  id: number
  ticket_no: string
  subject: string
  status: TicketStatus
  priority: TicketPriority
  customer: User
  assignee: User | null
  last_message_at: string | null
  created_at: string
}

export type Ticket = TicketListItem & {
  description: string
  updated_at: string
  message_count: number
}

export type TicketMessage = {
  id: number
  ticket_id: number
  body: string
  is_internal: boolean
  sender: User
  created_at: string
}

export type Page<T> = {
  items: T[]
  next_cursor: number | null
}
