import type { Collection } from '@/types'
import { apiRequest } from '@/lib/api'

// ---------------------------------------------------------------------------
// Raw backend response types (snake_case)
// ---------------------------------------------------------------------------

interface CollectionResponse {
  id: string
  name: string
  description: string | null
  report_count: number
  created_at: string
  updated_at: string
}

interface CollectionListResponse {
  items: CollectionResponse[]
  total: number
  skip: number
  limit: number
}

// ---------------------------------------------------------------------------
// Mappers
// ---------------------------------------------------------------------------

function mapCollection(c: CollectionResponse): Collection {
  return {
    id: c.id,
    name: c.name,
    description: c.description ?? undefined,
    reportCount: c.report_count,
    createdAt: c.created_at,
    updatedAt: c.updated_at,
  }
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export const CollectionService = {
  /** List all collections (paginated). */
  async list(
    params?: { limit?: number; offset?: number }
  ): Promise<Collection[]> {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    const data = await apiRequest<CollectionListResponse>(
      `/collections${qs ? '?' + qs : ''}`
    )
    return data.items.map(mapCollection)
  },

  /** Get a single collection by ID. */
  async getById(id: string): Promise<Collection> {
    const data = await apiRequest<CollectionResponse>(`/collections/${id}`)
    return mapCollection(data)
  },

  /** Create a new collection. */
  async create(data: {
    name: string
    description?: string
  }): Promise<Collection> {
    const result = await apiRequest<CollectionResponse>('/collections', {
      method: 'POST',
      body: {
        name: data.name,
        description: data.description,
      },
    })
    return mapCollection(result)
  },

  /** Update collection metadata. */
  async update(
    id: string,
    data: Partial<Collection>
  ): Promise<Collection> {
    const body: Record<string, unknown> = {}
    if (data.name !== undefined) body.name = data.name
    if (data.description !== undefined) body.description = data.description

    const result = await apiRequest<CollectionResponse>(
      `/collections/${id}`,
      { method: 'PATCH', body }
    )
    return mapCollection(result)
  },

  /** Delete a collection (does not delete member reports). */
  async delete(id: string): Promise<void> {
    await apiRequest(`/collections/${id}`, { method: 'DELETE' })
  },

  /** Get reports in a collection. */
  async getReports(_collectionId: string) {
    // Backend returns the collection including report_count but not report list.
    // This can be enhanced when the backend adds a report membership listing endpoint.
    return []
  },

  /** Add a report to a collection. */
  async addReport(collectionId: string, reportId: string): Promise<void> {
    await apiRequest(`/collections/${collectionId}/reports/${reportId}`, {
      method: 'POST',
    })
  },

  /** Remove a report from a collection. */
  async removeReport(
    collectionId: string,
    reportId: string
  ): Promise<void> {
    await apiRequest(`/collections/${collectionId}/reports/${reportId}`, {
      method: 'DELETE',
    })
  },
}
