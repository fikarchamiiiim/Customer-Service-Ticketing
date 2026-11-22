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
