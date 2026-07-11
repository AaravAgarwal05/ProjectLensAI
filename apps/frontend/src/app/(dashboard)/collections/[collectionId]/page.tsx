'use client'

import { use } from 'react'
import Link from 'next/link'
import { PageHeader } from '@/components/shared/page-header'
import { PageContainer } from '@/components/shared/page-container'
import { SectionCard } from '@/components/shared/section-card'
import { EmptyState } from '@/components/shared/empty-state'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FolderOpen, FileText, Plus, Trash2 } from 'lucide-react'
import { placeholderCollections, placeholderReports } from '@/lib/placeholders'

export default function CollectionDetailPage({
  params,
}: {
  params: Promise<{ collectionId: string }>
}) {
  const { collectionId } = use(params)
  const collection = placeholderCollections().find(
    (c) => c.id === collectionId
  )

  if (!collection) {
    return (
      <PageContainer>
        <PageHeader
          title="Collection not found"
          description={`No collection found with ID: ${collectionId}`}
          breadcrumbs={[
            { label: 'Collections', href: '/collections' },
            { label: 'Not Found' },
          ]}
        />
      </PageContainer>
    )
  }

  const reports = placeholderReports().slice(0, 3)

  return (
    <PageContainer>
      <PageHeader
        title={collection.name}
        description={collection.description}
        breadcrumbs={[
          { label: 'Collections', href: '/collections' },
          { label: collection.name },
        ]}
        icon={FolderOpen}
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            Add Reports
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Reports list */}
        <div className="lg:col-span-2">
          <SectionCard
            title="Reports"
            description={`${collection.reportCount} reports in collection`}
          >
            {reports.length === 0 ? (
              <EmptyState
                title="No reports in this collection"
                icon={FileText}
                action={<Button variant="secondary" size="sm"><Plus className="h-4 w-4" />Add Reports</Button>}
              />
            ) : (
              <div className="space-y-2">
                {reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between rounded-lg border border-surface-100 p-3 transition-colors hover:bg-surface-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-surface-100">
                        <FileText className="h-4 w-4 text-surface-500" />
                      </div>
                      <div>
                        <Link
                          href={`/reports/${report.id}`}
                          className="text-sm font-medium text-surface-900 hover:text-primary-600"
                        >
                          {report.title}
                        </Link>
                        <p className="text-xs text-surface-500">
                          {report.author} &middot;{' '}
                          {report.createdAt.slice(0, 10)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          report.status === 'ready' ? 'accent' : 'default'
                        }
                      >
                        {report.status}
                      </Badge>
                      <button className="rounded p-1.5 text-surface-400 hover:bg-surface-100 hover:text-red-500">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <SectionCard title="Collection Info">
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-surface-500">Created</span>
                <span className="text-surface-700">
                  {collection.createdAt.slice(0, 10)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-surface-500">Updated</span>
                <span className="text-surface-700">
                  {collection.updatedAt.slice(0, 10)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-surface-500">Reports</span>
                <span className="text-surface-700">
                  {collection.reportCount}
                </span>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Actions">
            <div className="space-y-2">
              <Button className="w-full" size="sm">
                <Plus className="h-4 w-4" />
                Add Reports
              </Button>
              <Button variant="secondary" className="w-full" size="sm">
                Open in Compare
              </Button>
              <Button variant="ghost" className="w-full" size="sm">
                <Trash2 className="h-4 w-4 text-red-500" />
                <span className="text-red-500">Delete Collection</span>
              </Button>
            </div>
          </SectionCard>
        </div>
      </div>
    </PageContainer>
  )
}
