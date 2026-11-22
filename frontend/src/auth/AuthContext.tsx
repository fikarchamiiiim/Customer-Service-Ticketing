import { createContext, useCallback, useContext, useMemo, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '../api/client'
import { fetchMe, loginDev, loginWithGoogle, logout as logoutRequest } from '../api/auth'
import type { User } from '../types'

type AuthState = {
  user: User | null
  isLoading: boolean
  loginGoogle: (idToken: string) => Promise<User>
  loginAsDev: (email: string) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  // Kunci cache 'me' adalah sumber kebenaran soal "siapa yang login".
  // 401 BUKAN error yang perlu ditampilkan -> dianggap "belum login".
  const { data, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: fetchMe,
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 60_000,
  })

  const loginGoogle = useCallback(
    async (idToken: string) => {
      const user = await loginWithGoogle(idToken)
      queryClient.setQueryData(['me'], user)
      return user
    },
    [queryClient],
  )

  const loginAsDev = useCallback(
    async (email: string) => {
      const user = await loginDev(email)
      queryClient.setQueryData(['me'], user)
      return user
    },
    [queryClient],
  )

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } catch (err) {
      // Kalau sesi ternyata sudah habis, logout tetap dianggap berhasil.
      if (!(err instanceof ApiError && err.isUnauthorized)) throw err
    }
    queryClient.setQueryData(['me'], null)
    queryClient.clear()
  }, [queryClient])

  const value = useMemo<AuthState>(
    () => ({
      user: data ?? null,
      isLoading,
      loginGoogle,
      loginAsDev,
      logout,
    }),
    [data, isLoading, loginGoogle, loginAsDev, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth harus dipakai di dalam <AuthProvider>')
  return ctx
}
