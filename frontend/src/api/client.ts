// Satu-satunya pintu keluar HTTP ke backend.
// Path selalu relatif ('/api/v1/...') supaya dev (Vite proxy) dan prod (nginx) sama-sama jalan.

export class ApiError extends Error {
  status: number
  code: string
  details: unknown

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }

  get isUnauthorized() {
    return this.status === 401
  }
}

type ErrorEnvelope = {
  error?: { code?: string; message?: string; details?: unknown }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    credentials: 'include', // cookie sesi ikut terkirim
  })

  if (res.status === 204) return undefined as T

  const text = await res.text()
  let body: unknown = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = null
  }

  if (!res.ok) {
    // Backend mengirim {"error": {"code","message","details"}}.
    // Kalau bentuknya lain (mis. proxy error HTML), tetap jangan crash.
    const err = (body as ErrorEnvelope | null)?.error ?? {}
    throw new ApiError(
      res.status,
      err.code ?? `HTTP_${res.status}`,
      err.message ?? `Request gagal (${res.status})`,
      err.details,
    )
  }

  return body as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: 'PATCH', body: data ? JSON.stringify(data) : undefined }),
}
