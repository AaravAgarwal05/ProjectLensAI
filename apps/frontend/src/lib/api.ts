/** API client placeholder — replace with real implementation. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

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

/** Stub fetch — throws NotImplementedError until real API is connected. */
export async function apiRequest<T>(
  _path: string,
  _options: ApiOptions = {}
): Promise<T> {
  // TODO: Replace with real fetch when backend is ready
  // const res = await fetch(`${API_BASE}${path}`, {
  //   method: options.method ?? 'GET',
  //   headers: { 'Content-Type': 'application/json', ...options.headers },
  //   body: options.body ? JSON.stringify(options.body) : undefined,
  // })
  // if (!res.ok) {
  //   const err = await res.json().catch(() => ({}))
  //   throw new ApiError(err.message ?? res.statusText, res.status, err.code)
  // }
  // return res.json()
  void _path
  void _options
  void API_BASE
  throw new Error(
    'apiRequest not implemented. Set NEXT_PUBLIC_API_URL and implement fetch.'
  )
}

/** Placeholder token getter — replace with real auth token logic. */
export function getAuthToken(): string | null {
  // TODO: get from auth store / cookie
  return null
}

/** Generate a placeholder list of items for UI scaffolding. */
export function generatePlaceholderList<T>(
  factory: (index: number) => T,
  count = 5
): T[] {
  return Array.from({ length: count }, (_, i) => factory(i))
}

/** Placeholder pagination for UI scaffolding. */
export function placeholderPage<T>(
  items: T[],
  page: number,
  pageSize: number
): { items: T[]; total: number; page: number; pageSize: number } {
  const start = (page - 1) * pageSize
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    pageSize,
  }
}
