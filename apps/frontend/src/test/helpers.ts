import { vi, type Mock } from 'vitest'

/** Build a JSON Response for the mocked fetch. */
export function jsonResponse(
  status: number,
  body: unknown,
  statusText = ''
): Response {
  return new Response(JSON.stringify(body), { status, statusText })
}

/** Stub global fetch with a mock and return it for assertion. */
export function mockFetch(): Mock {
  const fn = vi.fn()
  vi.stubGlobal('fetch', fn)
  return fn
}
