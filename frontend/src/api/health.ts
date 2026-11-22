import { api } from './client'

export type Health = {
  status: 'ok' | 'degraded'
  db: 'ok' | 'down'
  db_error: string | null
  version: string
}

export const fetchHealth = () => api.get<Health>('/api/v1/health')
