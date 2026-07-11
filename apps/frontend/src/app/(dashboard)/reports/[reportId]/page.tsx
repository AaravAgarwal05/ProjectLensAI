'use client'

import { use } from 'react'
import { PageHeader } from '@/components/shared/page-header'
import { PageContainer } from '@/components/shared/page-container'
import { SectionCard } from '@/components/shared/section-card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FileText, Download, Trash2, History, Clock, User, Tag } from 'lucide-react'
import { placeholderReports } from '@/lib/placeholders'

export default function ReportDetailPage({
  params,
}: {
  params: Promise<{ reportId: string }>
}) {
  const { reportId } = use(params)
  const report = placeholderReports().find((r) => r.id === reportId)

  if (!report) {
    return (
      <PageContainer>
        <PageHeader
          title="Report not found"
          description={`No report found with ID: ${reportId}`}
          breadcrumbs={[
            { label: 'Reports', href: '/reports' },
            { label: 'Not Found' },
          ]}
        />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title={report.title}
        description={report.description}
        breadcrumbs={[
          { label: 'Reports', href: '/reports' },
          { label: report.title },
        ]}
        icon={FileText}
        actions={
          <>
            <Button variant="secondary" size="sm">
              <Download className="h-4 w-4" />
              Download
            </Button>
            <Button variant="danger" size="sm">
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="space-y-6 lg:col-span-2">
          {/* Metadata */}
          <SectionCard title="Metadata">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  Author
                </p>
                <div className="mt-1 flex items-center gap-1.5 text-sm text-surface-700">
                  <User className="h-3.5 w-3.5 text-surface-400" />
                  {report.author}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  Department
                </p>
                <p className="mt-1 text-sm text-surface-700">
                  {report.department}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  Status
                </p>
                <Badge
                  className="mt-1"
                  variant={
                    report.status === 'ready'
                      ? 'accent'
                      : report.status === 'processing'
                        ? 'warning'
                        : 'danger'
                  }
                >
                  {report.status}
                </Badge>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  Visibility
                </p>
                <Badge className="mt-1">{report.visibility}</Badge>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  File size
                </p>
                <p className="mt-1 text-sm text-surface-700">
                  {(report.fileSize ?? 0 / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  Chunks
                </p>
                <p className="mt-1 text-sm text-surface-700">
                  {report.chunkCount}
                </p>
              </div>
              <div className="col-span-2">
                <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  Tags
                </p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {report.tags.map((tag) => (
                    <Badge key={tag} variant="default">
                      <Tag className="mr-1 h-3 w-3" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </SectionCard>

          {/* Versions */}
          <SectionCard title="Versions" description="Version history for this report">
            <div className="space-y-2">
              {[
                { version: 2, date: '2025-01-15', size: '2.5 MB', status: 'Current' },
                { version: 1, date: '2024-12-15', size: '2.4 MB', status: 'Archived' },
              ].map((v) => (
                <div
                  key={v.version}
                  className="flex items-center justify-between rounded-lg border border-surface-100 p-3"
                >
                  <div className="flex items-center gap-3">
                    <History className="h-4 w-4 text-surface-400" />
                    <div>
                      <p className="text-sm font-medium text-surface-700">
                        Version {v.version}
                      </p>
                      <p className="text-xs text-surface-500">
                        {v.date} &middot; {v.size}
                      </p>
                    </div>
                  </div>
                  <Badge variant={v.status === 'Current' ? 'accent' : 'default'}>
                    {v.status}
                  </Badge>
                </div>
              ))}
            </div>
          </SectionCard>

          {/* Processing Timeline */}
          <SectionCard title="Processing Timeline">
            <div className="space-y-4">
              {[
                { step: 'Uploaded', time: '2:30 PM', done: true },
                { step: 'Chunking', time: '2:31 PM', done: true },
                { step: 'Embedding', time: '2:32 PM', done: true },
                { step: 'Indexing', time: '2:33 PM', done: true },
                { step: 'Ready', time: '2:35 PM', done: true },
              ].map((step, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="flex flex-col items-center">
                    <div
                      className={`flex h-6 w-6 items-center justify-center rounded-full ${
                        step.done
                          ? 'bg-accent-100 text-accent-600'
                          : 'bg-surface-100 text-surface-400'
                      }`}
                    >
                      <Clock className="h-3.5 w-3.5" />
                    </div>
                    {i < 4 && (
                      <div className="h-4 w-0.5 bg-surface-200" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-surface-700">
                      {step.step}
                    </p>
                    <p className="text-xs text-surface-400">{step.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          <SectionCard title="Actions">
            <div className="space-y-2">
              <Button className="w-full" size="sm">
                <Download className="h-4 w-4" />
                Download Report
              </Button>
              <Button variant="secondary" className="w-full" size="sm">
                Open in Chat
              </Button>
              <Button variant="secondary" className="w-full" size="sm">
                Add to Collection
              </Button>
              <Button variant="ghost" className="w-full" size="sm">
                <Trash2 className="h-4 w-4 text-red-500" />
                <span className="text-red-500">Delete Report</span>
              </Button>
            </div>
          </SectionCard>

          {/* Info */}
          <SectionCard title="Details">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-surface-500">Created</span>
                <span className="text-surface-700">
                  {report.createdAt.slice(0, 10)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-surface-500">Updated</span>
                <span className="text-surface-700">
                  {report.updatedAt.slice(0, 10)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-surface-500">Year</span>
                <span className="text-surface-700">{report.year}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-surface-500">Type</span>
                <span className="text-surface-700">{report.mimeType}</span>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </PageContainer>
  )
}
