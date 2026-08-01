/**
 * API client for ProjectLens AI backend.
 * Uses fetch with `credentials: "include"` so the HttpOnly auth cookie is
 * sent automatically — no token is ever stored in localStorage.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3001/api/v1'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  headers?: Record<string, string>
}

/**
 * Make an authenticated request to the API.
 * The auth cookie travels with `credentials: "include"`; there is no
 * Authorization header and nothing to manage client-side.
 */
export async function apiRequest<T>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const headers: Record<string, string> = { ...options.headers }

  // Only set Content-Type for JSON bodies; let the browser handle FormData
  const isFormData =
    typeof FormData !== 'undefined' && options.body instanceof FormData
  if (options.body !== undefined && !isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  const body = isFormData
    ? (options.body as FormData)
    : options.body !== undefined
      ? JSON.stringify(options.body)
      : undefined

  const res = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body,
    credentials: 'include',
  })

  // 204 No Content — return undefined
  if (res.status === 204) {
    return undefined as T
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    // Backend wraps errors in { error: { message, code, details } }
    const errPayload = body?.error ?? body
    throw new ApiError(
      errPayload.detail ?? errPayload.message ?? res.statusText,
      res.status,
      errPayload.code
    )
  }

  return res.json()
}
