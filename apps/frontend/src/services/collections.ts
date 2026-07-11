import type { Collection, Report } from '@/types'
import { NotImplementedError } from './base'

export const CollectionService = {
  async list(): Promise<Collection[]> {
    throw new NotImplementedError('CollectionService', 'list')
  },

  async getById(_id: string): Promise<Collection> {
    throw new NotImplementedError('CollectionService', 'getById')
  },

  async create(_data: { name: string; description?: string }): Promise<Collection> {
    throw new NotImplementedError('CollectionService', 'create')
  },

  async update(
    _id: string,
    _data: Partial<Collection>
  ): Promise<Collection> {
    throw new NotImplementedError('CollectionService', 'update')
  },

  async delete(_id: string): Promise<void> {
    throw new NotImplementedError('CollectionService', 'delete')
  },

  async getReports(_collectionId: string): Promise<Report[]> {
    throw new NotImplementedError('CollectionService', 'getReports')
  },

  async addReport(_collectionId: string, _reportId: string): Promise<void> {
    throw new NotImplementedError('CollectionService', 'addReport')
  },

  async removeReport(_collectionId: string, _reportId: string): Promise<void> {
    throw new NotImplementedError('CollectionService', 'removeReport')
  },
}
