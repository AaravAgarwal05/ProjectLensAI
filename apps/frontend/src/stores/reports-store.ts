import { create } from 'zustand'
import type { Report, ReportFilters } from '@/types'

interface ReportsState {
  reports: Report[]
  selectedReport: Report | null
  filters: ReportFilters
  isLoading: boolean
  total: number
  page: number
  pageSize: number
  setReports: (reports: Report[]) => void
  setSelectedReport: (report: Report | null) => void
  setFilters: (filters: Partial<ReportFilters>) => void
  setLoading: (loading: boolean) => void
  setPage: (page: number) => void
}

export const useReportsStore = create<ReportsState>((set) => ({
  reports: [],
  selectedReport: null,
  filters: { page: 1, pageSize: 10 },
  isLoading: false,
  total: 0,
  page: 1,
  pageSize: 10,
  setReports: (reports) => set({ reports }),
  setSelectedReport: (selectedReport) => set({ selectedReport }),
  setFilters: (filters) =>
    set((s) => ({ filters: { ...s.filters, ...filters } })),
  setLoading: (isLoading) => set({ isLoading }),
  setPage: (page) => set({ page }),
}))
