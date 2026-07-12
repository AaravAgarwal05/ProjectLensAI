/**
 * API client for ProjectLens AI backend.
 * Uses fetch directly with auth token management.
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

/** Read auth token from localStorage. */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

/** Persist auth token to localStorage. */
export function setAuthToken(token: string): void {
  localStorage.setItem('auth_token', token)
}

/** Remove auth token from localStorage. */
export function clearAuthToken(): void {
  localStorage.removeItem('auth_token')
}

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  headers?: Record<string, string>
}

/**
 * Make an authenticated request to the API.
 * Handles JSON serialisation, auth headers, 401 redirect, and 204 empty responses.
 */
export async function apiRequest<T>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const token = getAuthToken()
  const headers: Record<string, string> = { ...options.headers }

  // Only set Content-Type for JSON bodies; let the browser handle FormData
  const isFormData =
    typeof FormData !== 'undefined' && options.body instanceof FormData
  if (options.body !== undefined && !isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
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
