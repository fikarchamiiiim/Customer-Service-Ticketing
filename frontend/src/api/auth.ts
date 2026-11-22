import { api } from './client'
import type { DevConfig, User } from '../types'

export const fetchMe = () => api.get<User>('/api/v1/me')

export const fetchDevConfig = () => api.get<DevConfig>('/api/v1/dev/config')

export const loginWithGoogle = (idToken: string) =>
  api.post<User>('/api/v1/auth/google', { id_token: idToken })

export const loginDev = (email: string) => api.post<User>('/api/v1/auth/dev-login', { email })

export const logout = () => api.post<void>('/api/v1/auth/logout')
