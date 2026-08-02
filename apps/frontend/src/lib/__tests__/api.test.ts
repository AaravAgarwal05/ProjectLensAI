import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE, apiRequest } from '@/lib/api'
import { jsonResponse, mockFetch } from '@/test/helpers'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('apiRequest', () => {
  it('sends GET with credentials include and no body', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { ok: true }))

    await apiRequest('/reports')

    expect(fn).toHaveBeenCalledWith(
      `${API_BASE}/reports`,
      expect.objectContaining({
        method: 'GET',
        headers: {},
        body: undefined,
        credentials: 'include',
      })
    )
  })

  it('serializes JSON bodies and sets Content-Type', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, {}))

    await apiRequest('/reports', { method: 'POST', body: { title: 'X' } })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(init.body).toBe(JSON.stringify({ title: 'X' }))
  })

  it('does not set Content-Type for FormData bodies', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, {}))

    const fd = new FormData()
    fd.append('file', 'x')
    await apiRequest('/reports', { method: 'POST', body: fd })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.headers).toEqual({})
    expect(init.body).toBe(fd)
  })

  it('returns undefined for 204 No Content', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(new Response(null, { status: 204 }))

    const result = await apiRequest<never>('/reports/1', { method: 'DELETE' })
    expect(result).toBeUndefined()
  })

  it('throws ApiError from the error envelope', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(400, { error: { message: 'Bad', code: 'invalid_input' } }, 'Bad Request')
    )

    await expect(apiRequest('/reports')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      code: 'invalid_input',
      message: 'Bad',
    })
  })

  it('prefers detail over message in the error payload', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(422, { detail: 'detailed', message: 'short', code: 'c' })
    )

    await expect(apiRequest('/reports')).rejects.toMatchObject({
      message: 'detailed',
      code: 'c',
    })
  })

  it('falls back to statusText when the error body is not JSON', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      new Response('oops', { status: 500, statusText: 'Internal Server Error' })
    )

    await expect(apiRequest('/reports')).rejects.toMatchObject({
      name: 'ApiError',
      status: 500,
      message: 'Internal Server Error',
    })
  })

  it('returns parsed JSON on success', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { id: 'r1', title: 'T' }))

    const data = await apiRequest<{ id: string; title: string }>('/reports/r1')
    expect(data).toEqual({ id: 'r1', title: 'T' })
  })
})
