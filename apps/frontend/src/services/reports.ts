import type { Report, ReportFilters, ReportVersion } from '@/types'
import { NotImplementedError } from './base'

export const ReportService = {
  async list(_filters?: ReportFilters): Promise<{
    items: Report[]
    total: number
    page: number
    pageSize: number
  }> {
    throw new NotImplementedError('ReportService', 'list')
  },

  async getById(_id: string): Promise<Report> {
    throw new NotImplementedError('ReportService', 'getById')
  },

  async upload(_file: File, _metadata?: Partial<Report>): Promise<Report> {
    throw new NotImplementedError('ReportService', 'upload')
  },

  async update(
    _id: string,
    _data: Partial<Report>
  ): Promise<Report> {
    throw new NotImplementedError('ReportService', 'update')
  },

  async delete(_id: string): Promise<void> {
    throw new NotImplementedError('ReportService', 'delete')
  },

  async getVersions(_reportId: string): Promise<ReportVersion[]> {
    throw new NotImplementedError('ReportService', 'getVersions')
  },

  async getChunkCount(_reportId: string): Promise<number> {
    throw new NotImplementedError('ReportService', 'getChunkCount')
  },
}
