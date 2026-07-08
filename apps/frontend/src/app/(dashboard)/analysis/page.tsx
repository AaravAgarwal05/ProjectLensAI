'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  BarChart3,
  Plus,
  Search,
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
} from 'lucide-react'

type AnalysisStatus = 'completed' | 'processing' | 'failed'

interface Analysis {
  id: string
  documentName: string
  type: string
  date: string
  status: AnalysisStatus
  summary: string
}

const analyses: Analysis[] = [
  {
    id: '1',
    documentName: 'Q4 Financial Report.pdf',
    type: 'Financial Analysis',
    date: '2026-07-04',
    status: 'completed',
    summary: 'Revenue growth analysis with key driver breakdown',
  },
  {
    id: '2',
    documentName: 'Market Research 2024.docx',
    type: 'Market Analysis',
    date: '2026-07-03',
    status: 'completed',
    summary: 'Competitive landscape and market positioning',
  },
  {
    id: '3',
    documentName: 'Contract Draft v3.docx',
    type: 'Contract Review',
    date: '2026-07-03',
    status: 'processing',
    summary: 'Clause-by-clause analysis with risk assessment',
  },
  {
    id: '4',
    documentName: 'Competitor Analysis.xlsx',
    type: 'Competitive Analysis',
    date: '2026-07-02',
    status: 'completed',
    summary: 'Pricing comparison and feature gap analysis',
  },
  {
    id: '5',
    documentName: 'Employee Handbook.pdf',
    type: 'Policy Review',
    date: '2026-06-28',
    status: 'failed',
    summary: 'Policy compliance and consistency check',
  },
]

const statusConfig: Record<AnalysisStatus, { icon: typeof Clock; label: string; classes: string }> = {
  completed: {
    icon: CheckCircle2,
    label: 'Completed',
    classes: 'bg-accent-50 text-accent-700 ring-accent-600/20',
  },
  processing: {
    icon: Clock,
    label: 'Processing',
    classes: 'bg-yellow-50 text-yellow-700 ring-yellow-600/20',
  },
  failed: {
    icon: AlertCircle,
    label: 'Failed',
    classes: 'bg-red-50 text-red-700 ring-red-600/20',
  },
}

export default function AnalysisPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const filtered = analyses.filter((a) =>
    a.documentName.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-surface-900">
            Analysis
          </h1>
          <p className="mt-1 text-sm text-surface-500">
            View and manage document analyses
          </p>
        </div>
        <button className="btn-primary">
          <Plus className="h-4 w-4" />
          New Analysis
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
        <input
          type="text"
          placeholder="Search analyses..."
          className="input-field pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Analysis List */}
      <div className="space-y-4">
        {filtered.map((analysis) => {
          const status = statusConfig[analysis.status]
          const StatusIcon = status.icon
          return (
            <div key={analysis.id} className="card">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
                    <BarChart3 className="h-5 w-5 text-primary-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-surface-900">
                        {analysis.type}
                      </h3>
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${status.classes}`}
                      >
                        <StatusIcon className="h-3 w-3" />
                        {status.label}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-surface-500">
                      {analysis.summary}
                    </p>
                    <div className="mt-2 flex items-center gap-3 text-xs text-surface-400">
                      <span className="inline-flex items-center gap-1">
                        <FileText className="h-3 w-3" />
                        {analysis.documentName}
                      </span>
                      <span>{analysis.date}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:shrink-0">
                  {analysis.status === 'completed' && (
                    <Link
                      href={`/dashboard/documents/${analysis.id}`}
                      className="btn-secondary text-sm"
                    >
                      View Results
                    </Link>
                  )}
                  {analysis.status === 'failed' && (
                    <button className="btn-secondary text-sm">
                      Retry
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}

        {filtered.length === 0 && (
          <div className="py-16 text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-surface-300" />
            <p className="mt-4 text-sm text-surface-500">
              No analyses found
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
