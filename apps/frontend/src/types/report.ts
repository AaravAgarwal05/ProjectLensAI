export type ReportStatus =
  | 'uploading'
  | 'processing'
  | 'ready'
  | 'error'
  | 'deleted'

export type ReportVisibility = 'private' | 'public' | 'team'

export interface Report {
  id: string
  title: string
  description?: string
  department?: string
  author?: string
  tags: string[]
  visibility: ReportVisibility
  year?: number
  status: ReportStatus
  fileSize?: number
  mimeType?: string
  chunkCount?: number
  storagePath?: string
  originalFilename?: string
  checksum?: string
  createdAt: string
  updatedAt: string
}

export interface ReportVersion {
  id: string
  reportId: string
  versionNumber: number
  storagePath: string
  originalFilename: string
  mimeType: string
  checksum: string
  fileSize: number
  createdAt: string
}

export interface ReportFilters {
  search?: string
  status?: ReportStatus
  department?: string
  author?: string
  tags?: string[]
  visibility?: ReportVisibility
  year?: number
  page: number
  pageSize: number
}
