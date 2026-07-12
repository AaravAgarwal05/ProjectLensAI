import type { Report, ReportFilters, ReportVersion } from '@/types'
import { apiRequest, API_BASE, getAuthToken, ApiError } from '@/lib/api'

// ---------------------------------------------------------------------------
// Raw backend response types (snake_case)
// ---------------------------------------------------------------------------

interface VersionResponse {
  id: string
  version_number: number
  original_filename: string
  mime_type: string
  file_size: number
  created_at: string
}

interface ReportResponse {
  id: string
  title: string
  description: string | null
  department: string | null
  author: string | null
  tags: string[] | null
  visibility: string
  year: number | null
  status: string
  original_filename: string | null
  mime_type: string | null
  checksum: string | null
  file_size: number | null
  versions: VersionResponse[]
  created_at: string
  updated_at: string
}

interface ReportListResponse {
  items: ReportResponse[]
  total: number
  skip: number
  limit: number
}

// ---------------------------------------------------------------------------
// Mappers
// ---------------------------------------------------------------------------

function mapReport(r: ReportResponse): Report {
  return {
    id: r.id,
    title: r.title,
    description: r.description ?? undefined,
    department: r.department ?? undefined,
    author: r.author ?? undefined,
    tags: r.tags ?? [],
    visibility: r.visibility as Report['visibility'],
    year: r.year ?? undefined,
    status: r.status as Report['status'],
    fileSize: r.file_size ?? undefined,
    mimeType: r.mime_type ?? undefined,
    checksum: r.checksum ?? undefined,
    originalFilename: r.original_filename ?? undefined,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  }
}

function mapVersion(v: VersionResponse, reportId: string): ReportVersion {
  return {
    id: v.id,
    reportId,
    versionNumber: v.version_number,
    storagePath: '',
    originalFilename: v.original_filename,
    mimeType: v.mime_type,
    checksum: '',
    fileSize: v.file_size,
    createdAt: v.created_at,
  }
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export const ReportService = {
  /** List reports with optional filters and pagination. */
  async list(
    filters?: ReportFilters
  ): Promise<{
    items: Report[]
    total: number
    page: number
    pageSize: number
  }> {
    const query = new URLSearchParams()
    if (filters) {
      const pageSize = filters.pageSize ?? 20
      query.set('skip', String((filters.page - 1) * pageSize))
      query.set('limit', String(pageSize))
      if (filters.status) query.set('status', filters.status)
      if (filters.author) query.set('author', filters.author)
      if (filters.search) query.set('search', filters.search)
    }
    const qs = query.toString()
    const data = await apiRequest<ReportListResponse>(
      `/reports${qs ? '?' + qs : ''}`
    )
    return {
      items: data.items.map(mapReport),
      total: data.total,
      page: Math.floor(data.skip / (data.limit || 20)) + 1,
      pageSize: data.limit,
    }
  },

  /** Get a single report by ID. */
  async getById(id: string): Promise<Report> {
    const data = await apiRequest<ReportResponse>(`/reports/${id}`)
    return mapReport(data)
  },

  /** Upload a new report file with metadata. */
  async upload(
    file: File,
    metadata?: Partial<Report>
  ): Promise<Report> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', metadata?.title ?? file.name)
    if (metadata?.description) formData.append('description', metadata.description)
    if (metadata?.department) formData.append('department', metadata.department)
    if (metadata?.author) formData.append('author', metadata.author)
    if (metadata?.visibility) formData.append('visibility', metadata.visibility)
    if (metadata?.year) formData.append('year', String(metadata.year))
    if (metadata?.tags?.length) formData.append('tags', metadata.tags.join(','))

    // Multipart upload — use raw fetch so the browser sets the Content-Type
    const token = getAuthToken()
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}/reports`, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (!res.ok) {
      if (res.status === 401) {
        if (typeof window !== 'undefined') window.location.href = '/login'
      }
      const err = await res.json().catch(() => ({}))
      throw new ApiError(
        err.detail ?? err.message ?? res.statusText,
        res.status,
        err.code
      )
    }

    const data: ReportResponse = await res.json()
    return mapReport(data)
  },

  /** Partially update report metadata. */
  async update(id: string, data: Partial<Report>): Promise<Report> {
    const body: Record<string, unknown> = {}
    if (data.title !== undefined) body.title = data.title
    if (data.description !== undefined) body.description = data.description
    if (data.department !== undefined) body.department = data.department
    if (data.author !== undefined) body.author = data.author
    if (data.tags !== undefined) body.tags = data.tags
    if (data.visibility !== undefined) body.visibility = data.visibility
    if (data.year !== undefined) body.year = data.year
    if (data.status !== undefined) body.status = data.status

    const result = await apiRequest<ReportResponse>(`/reports/${id}`, {
      method: 'PATCH',
      body,
    })
    return mapReport(result)
  },

  /** Delete a report. */
  async delete(id: string): Promise<void> {
    await apiRequest(`/reports/${id}`, { method: 'DELETE' })
  },

  /** List all versions of a report. */
  async getVersions(reportId: string): Promise<ReportVersion[]> {
    const data = await apiRequest<VersionResponse[]>(
      `/reports/${reportId}/versions`
    )
    return data.map((v) => mapVersion(v, reportId))
  },

  /** Get chunk count for a report — not yet available via API. */
  async getChunkCount(_reportId: string): Promise<number> {
    return 0
  },
}
