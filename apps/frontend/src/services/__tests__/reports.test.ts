import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE } from '@/lib/api'
import { ReportService } from '@/services/reports'
import { jsonResponse, mockFetch } from '@/test/helpers'

afterEach(() => {
  vi.unstubAllGlobals()
})

const RAW_REPORT = {
  id: 'r1',
  title: 'Annual Report',
  description: null,
  department: 'Finance',
  author: null,
  tags: ['finance'],
  visibility: 'internal',
  year: 2025,
  status: 'ready',
  original_filename: 'annual.pdf',
  mime_type: 'application/pdf',
  checksum: 'abc',
  file_size: 100,
  versions: [],
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z',
}

describe('ReportService.list', () => {
  it('maps items to camelCase and derives page/pageSize', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(200, {
        items: [RAW_REPORT],
        total: 42,
        skip: 10,
        limit: 10,
      })
    )

    const result = await ReportService.list({ page: 2, pageSize: 10 })

    expect(result.total).toBe(42)
    expect(result.page).toBe(2)
    expect(result.pageSize).toBe(10)
    expect(result.items[0]).toMatchObject({
      id: 'r1',
      title: 'Annual Report',
      department: 'Finance',
      tags: ['finance'],
      year: 2025,
      status: 'ready',
      originalFilename: 'annual.pdf',
      fileSize: 100,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-02T00:00:00Z',
    })
    expect(result.items[0]?.description).toBeUndefined()
    expect(result.items[0]?.author).toBeUndefined()
  })

  it('builds skip/limit from page/pageSize and appends filters', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { items: [], total: 0, skip: 0, limit: 20 }))

    await ReportService.list({ page: 3, pageSize: 5, status: 'ready', author: 'Smith', search: 'Q4' })

    const [url] = fn.mock.calls[0] as [string]
    expect(url).toBe(
      `${API_BASE}/reports?skip=10&limit=5&status=ready&author=Smith&search=Q4`
    )
  })

  it('omits the query string when no filters are given', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { items: [], total: 0, skip: 0, limit: 20 }))

    await ReportService.list()

    const [url] = fn.mock.calls[0] as [string]
    expect(url).toBe(`${API_BASE}/reports`)
  })
})

describe('ReportService.getById', () => {
  it('maps a single report', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, RAW_REPORT))

    const report = await ReportService.getById('r1')

    expect(fn).toHaveBeenCalledWith(`${API_BASE}/reports/r1`, expect.any(Object))
    expect(report.id).toBe('r1')
    expect(report.originalFilename).toBe('annual.pdf')
  })
})

describe('ReportService.upload', () => {
  it('posts a multipart FormData via raw fetch', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(201, RAW_REPORT))

    const file = new File(['content'], 'annual.pdf', { type: 'application/pdf' })
    const report = await ReportService.upload(file, { title: 'My Report', visibility: 'private' })

    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE}/reports`)
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
    expect(init.headers).toBeUndefined() // browser sets multipart boundary

    const fd = init.body as FormData
    expect(fd.get('file')).toBe(file)
    expect(fd.get('title')).toBe('My Report')
    expect(fd.get('visibility')).toBe('private')

    expect(report.id).toBe('r1')
  })

  it('defaults the title to the file name', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(201, RAW_REPORT))

    const file = new File(['content'], 'untitled.pdf', { type: 'application/pdf' })
    await ReportService.upload(file)

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect((init.body as FormData).get('title')).toBe('untitled.pdf')
  })

  it('throws ApiError with the backend code on failure', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(413, { detail: 'too big', code: 'file_too_large' }, 'Payload Too Large')
    )

    const file = new File(['content'], 'big.pdf', { type: 'application/pdf' })
    const err = await ReportService.upload(file).catch((e) => e)

    expect(err.status).toBe(413)
    expect(err.code).toBe('file_too_large')
    expect(err.message).toBe('too big')
  })
})

describe('ReportService.update', () => {
  it('PATCHes only defined fields', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { ...RAW_REPORT, title: 'New Title' }))

    const report = await ReportService.update('r1', { title: 'New Title' })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('PATCH')
    expect(init.body).toBe(JSON.stringify({ title: 'New Title' }))
    expect(report.title).toBe('New Title')
  })
})

describe('ReportService.delete / deleteMany / getVersions', () => {
  it('delete sends DELETE and returns void', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(ReportService.delete('r1')).resolves.toBeUndefined()
    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE}/reports/r1`)
    expect(init.method).toBe('DELETE')
  })

  it('deleteMany deletes each id', async () => {
    const del = vi.spyOn(ReportService, 'delete').mockResolvedValue(undefined)

    await ReportService.deleteMany(['a', 'b', 'c'])

    expect(del).toHaveBeenCalledTimes(3)
    expect(del).toHaveBeenCalledWith('a')
    expect(del).toHaveBeenCalledWith('c')
  })

  it('getVersions maps version fields and threads reportId', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(200, [
        { id: 'v1', version_number: 2, original_filename: 'v2.pdf', mime_type: 'application/pdf', file_size: 5, created_at: '2025-01-01T00:00:00Z' },
      ])
    )

    const versions = await ReportService.getVersions('r1')

    expect(versions[0]).toMatchObject({
      id: 'v1',
      reportId: 'r1',
      versionNumber: 2,
      originalFilename: 'v2.pdf',
      fileSize: 5,
    })
  })
})
