import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE } from '@/lib/api'
import { CollectionService } from '@/services/collections'
import { jsonResponse, mockFetch } from '@/test/helpers'

afterEach(() => {
  vi.unstubAllGlobals()
})

const RAW_COLLECTION = {
  id: 'c1',
  name: 'Finance',
  description: 'Annual docs',
  report_count: 3,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z',
}

describe('CollectionService.list', () => {
  it('maps items and converts report_count → reportCount', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(200, { items: [RAW_COLLECTION], total: 1, skip: 0, limit: 20 })
    )

    const result = await CollectionService.list()

    expect(result[0]).toMatchObject({
      id: 'c1',
      name: 'Finance',
      description: 'Annual docs',
      reportCount: 3,
    })
  })

  it('appends limit/offset query params', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { items: [], total: 0, skip: 0, limit: 5 }))

    await CollectionService.list({ limit: 5, offset: 10 })

    const [url] = fn.mock.calls[0] as [string]
    expect(url).toBe(`${API_BASE}/collections?limit=5&offset=10`)
  })
})

describe('CollectionService.create', () => {
  it('POSTs name and description', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(201, RAW_COLLECTION))

    const result = await CollectionService.create({ name: 'Finance', description: 'Annual docs' })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ name: 'Finance', description: 'Annual docs' }))
    expect(result.id).toBe('c1')
  })
})

describe('CollectionService.update', () => {
  it('PATCHes only defined fields', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { ...RAW_COLLECTION, name: 'Updated' }))

    const result = await CollectionService.update('c1', { name: 'Updated' })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('PATCH')
    expect(init.body).toBe(JSON.stringify({ name: 'Updated' }))
    expect(result.name).toBe('Updated')
  })
})

describe('CollectionService.delete / addReport / removeReport', () => {
  it('delete sends DELETE', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(new Response(null, { status: 204 }))

    await CollectionService.delete('c1')

    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE}/collections/c1`)
    expect(init.method).toBe('DELETE')
  })

  it('addReport POSTs the nested report route', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, {}))

    await CollectionService.addReport('c1', 'r1')

    expect(fn).toHaveBeenCalledWith(
      `${API_BASE}/collections/c1/reports/r1`,
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('removeReport DELETEs the nested report route', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, {}))

    await CollectionService.removeReport('c1', 'r1')

    expect(fn).toHaveBeenCalledWith(
      `${API_BASE}/collections/c1/reports/r1`,
      expect.objectContaining({ method: 'DELETE' })
    )
  })
})
