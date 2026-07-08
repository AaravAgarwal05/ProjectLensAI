'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  FileText,
  Upload,
  Search,
  MoreVertical,
  Download,
  Trash2,
  Eye,
} from 'lucide-react'

const documents = [
  {
    id: '1',
    name: 'Q4 Financial Report.pdf',
    type: 'PDF',
    size: '2.4 MB',
    status: 'ready' as const,
    date: '2026-07-04',
  },
  {
    id: '2',
    name: 'Market Research 2024.docx',
    type: 'DOCX',
    size: '1.8 MB',
    status: 'ready' as const,
    date: '2026-07-03',
  },
  {
    id: '3',
    name: 'Contract Draft v3.docx',
    type: 'DOCX',
    size: '856 KB',
    status: 'processing' as const,
    date: '2026-07-03',
  },
  {
    id: '4',
    name: 'Competitor Analysis.xlsx',
    type: 'XLSX',
    size: '3.2 MB',
    status: 'ready' as const,
    date: '2026-07-02',
  },
  {
    id: '5',
    name: 'Product Roadmap 2025.pdf',
    type: 'PDF',
    size: '1.1 MB',
    status: 'failed' as const,
    date: '2026-07-01',
  },
  {
    id: '6',
    name: 'Employee Handbook.pdf',
    type: 'PDF',
    size: '4.5 MB',
    status: 'ready' as const,
    date: '2026-06-28',
  },
]

const statusConfig = {
  ready: {
    label: 'Ready',
    classes: 'bg-accent-50 text-accent-700 ring-accent-600/20',
  },
  processing: {
    label: 'Processing',
    classes: 'bg-yellow-50 text-yellow-700 ring-yellow-600/20',
  },
  failed: {
    label: 'Failed',
    classes: 'bg-red-50 text-red-700 ring-red-600/20',
  },
}

export default function DocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const filtered = documents.filter((doc) =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-surface-900">
            Documents
          </h1>
          <p className="mt-1 text-sm text-surface-500">
            Manage and analyze your documents
          </p>
        </div>
        <button className="btn-primary">
          <Upload className="h-4 w-4" />
          Upload Document
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
        <input
          type="text"
          placeholder="Search documents..."
          className="input-field pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Documents Table */}
      <div className="overflow-hidden rounded-xl border border-surface-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-surface-200">
          <thead>
            <tr className="bg-surface-50">
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500">
                Name
              </th>
              <th className="hidden px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500 sm:table-cell">
                Type
              </th>
              <th className="hidden px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500 md:table-cell">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500">
                Status
              </th>
              <th className="hidden px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500 lg:table-cell">
                Date
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-surface-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-200">
            {filtered.map((doc) => {
              const status = statusConfig[doc.status]
              return (
                <tr
                  key={doc.id}
                  className="transition-colors hover:bg-surface-50"
                >
                  <td className="px-6 py-4">
                    <Link
                      href={`/dashboard/documents/${doc.id}`}
                      className="flex items-center gap-3"
                    >
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50">
                        <FileText className="h-4 w-4 text-primary-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-surface-900 hover:text-primary-600">
                          {doc.name}
                        </p>
                        <p className="text-xs text-surface-400 sm:hidden">
                          {doc.type} &middot; {doc.size}
                        </p>
                      </div>
                    </Link>
                  </td>
                  <td className="hidden px-6 py-4 sm:table-cell">
                    <span className="text-sm text-surface-600">{doc.type}</span>
                  </td>
                  <td className="hidden px-6 py-4 md:table-cell">
                    <span className="text-sm text-surface-600">{doc.size}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${status.classes}`}
                    >
                      {status.label}
                    </span>
                  </td>
                  <td className="hidden px-6 py-4 lg:table-cell">
                    <span className="text-sm text-surface-600">{doc.date}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button className="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-600">
                        <Eye className="h-4 w-4" />
                      </button>
                      <button className="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-600">
                        <Download className="h-4 w-4" />
                      </button>
                      <button className="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-100 hover:text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-surface-300" />
            <p className="mt-4 text-sm text-surface-500">
              No documents found
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
