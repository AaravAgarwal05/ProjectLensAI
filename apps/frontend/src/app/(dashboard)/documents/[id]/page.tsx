'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  FileText,
  ArrowLeft,
  Download,
  Trash2,
  FileJson,
  AlignLeft,
  BarChart3,
  MessageSquare,
  Calendar,
  HardDrive,
  Tag,
} from 'lucide-react'

const tabs = [
  { id: 'overview', label: 'Overview', icon: FileJson },
  { id: 'content', label: 'Content', icon: AlignLeft },
  { id: 'analysis', label: 'Analysis', icon: BarChart3 },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
] as const

type TabId = (typeof tabs)[number]['id']

export default function DocumentDetailPage() {
  const params = useParams()
  const [activeTab, setActiveTab] = useState<TabId>('overview')

  const document = {
    name: 'Q4 Financial Report.pdf',
    type: 'PDF',
    size: '2.4 MB',
    pages: 12,
    status: 'Ready',
    createdAt: '2026-07-04',
    updatedAt: '2026-07-04',
    tags: ['financial', 'Q4', 'report'],
    description:
      'Quarterly financial report for Q4 2025, including revenue breakdown, expense analysis, and projections for the upcoming year.',
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <Link
          href="/dashboard/documents"
          className="inline-flex items-center gap-1 text-surface-500 transition-colors hover:text-surface-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Documents
        </Link>
        <span className="text-surface-300">/</span>
        <span className="font-medium text-surface-900 truncate max-w-xs">
          {document.name}
        </span>
      </div>

      {/* Document Header */}
      <div className="card">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-primary-50">
              <FileText className="h-7 w-7 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-surface-900">
                {document.name}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-surface-500">
                <span className="inline-flex items-center gap-1">
                  <Tag className="h-3.5 w-3.5" />
                  {document.type}
                </span>
                <span className="inline-flex items-center gap-1">
                  <HardDrive className="h-3.5 w-3.5" />
                  {document.size}
                </span>
                <span className="inline-flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {document.createdAt}
                </span>
                <span className="inline-flex rounded-full bg-accent-50 px-2.5 py-0.5 text-xs font-medium text-accent-700">
                  {document.status}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="btn-secondary">
              <Download className="h-4 w-4" />
              Download
            </button>
            <button className="rounded-lg border border-red-200 bg-white p-2.5 text-red-500 transition-colors hover:bg-red-50">
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-surface-200">
        <nav className="-mb-px flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-surface-500 hover:border-surface-300 hover:text-surface-700'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="card">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-surface-900 uppercase tracking-wider">
                Description
              </h3>
              <p className="mt-2 text-sm leading-6 text-surface-600">
                {document.description}
              </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-surface-900 uppercase tracking-wider">
                  Metadata
                </h3>
                <dl className="mt-3 space-y-3">
                  {[
                    { label: 'File Name', value: document.name },
                    { label: 'File Type', value: document.type },
                    { label: 'File Size', value: document.size },
                    { label: 'Pages', value: String(document.pages) },
                    { label: 'Created', value: document.createdAt },
                    { label: 'Last Modified', value: document.updatedAt },
                  ].map((item) => (
                    <div key={item.label} className="flex justify-between">
                      <dt className="text-sm text-surface-500">
                        {item.label}
                      </dt>
                      <dd className="text-sm font-medium text-surface-900">
                        {item.value}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-surface-900 uppercase tracking-wider">
                  Tags
                </h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {document.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center rounded-full bg-surface-100 px-3 py-1 text-xs font-medium text-surface-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-surface-900 uppercase tracking-wider">
                Content Preview
              </h3>
              <div className="mt-3 rounded-lg border border-surface-200 bg-surface-50 p-4">
                <p className="text-sm leading-7 text-surface-600">
                  {Array(8)
                    .fill(
                      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.',
                    )
                    .join(' ')}
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'content' && (
          <div className="space-y-4">
            <p className="text-sm text-surface-500">
              Full document content will appear here with text extraction and
              formatting preservation.
            </p>
            <div className="space-y-4 text-sm leading-7 text-surface-700">
              {Array(5)
                .fill(
                  'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.',
                )
                .map((text, i) => (
                  <p key={i}>{text}</p>
                ))}
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <p className="text-sm text-surface-500">
                AI-powered analysis results for this document.
              </p>
              <button className="btn-primary">
                <BarChart3 className="h-4 w-4" />
                Run Analysis
              </button>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                { label: 'Key Topics', items: ['Revenue Growth', 'Cost Reduction', 'Market Expansion', 'Risk Factors'] },
                { label: 'Sentiment', items: ['Overall: Positive', 'Confidence: 87%', 'Risk Level: Low'] },
                { label: 'Entities Found', items: ['12 People', '5 Companies', '3 Locations', '8 Metrics'] },
                { label: 'Summary', items: ['4.2x faster than manual review', '92% accuracy rate', '2 pages condensed'] },
              ].map((section) => (
                <div key={section.label} className="rounded-lg border border-surface-200 p-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-surface-500">
                    {section.label}
                  </h4>
                  <ul className="mt-3 space-y-1.5">
                    {section.items.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-sm text-surface-700">
                        <span className="h-1.5 w-1.5 rounded-full bg-primary-400" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-surface-100">
              <MessageSquare className="h-7 w-7 text-surface-400" />
            </div>
            <h3 className="text-lg font-semibold text-surface-900">
              Chat about this document
            </h3>
            <p className="mt-2 max-w-sm text-center text-sm text-surface-500">
              Ask questions about this document and get AI-powered answers
              based on its content.
            </p>
            <Link
              href={`/dashboard/chat?document=${params.id}`}
              className="btn-primary mt-6"
            >
              Open Chat
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
