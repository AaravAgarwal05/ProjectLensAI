'use client'

import { PageHeader } from '@/components/shared/page-header'
import { PageContainer } from '@/components/shared/page-container'
import { SectionCard } from '@/components/shared/section-card'
import { EmptyState } from '@/components/shared/empty-state'
import { Button } from '@/components/ui/button'
import { GitCompare, Plus, FileText } from 'lucide-react'
import { placeholderReports } from '@/lib/placeholders'

export default function ComparePage() {
  const reports = placeholderReports().slice(0, 2)

  return (
    <PageContainer>
      <PageHeader
        title="Compare"
        description="Compare documents side by side"
        breadcrumbs={[{ label: 'Compare' }]}
        icon={GitCompare}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left panel */}
        <SectionCard
          title="Document A"
          action={
            <Button variant="secondary" size="sm">
              <Plus className="h-4 w-4" />
              Select
            </Button>
          }
        >
          {reports[0] ? (
            <div className="flex items-center gap-3 rounded-lg border border-surface-100 bg-surface-50/50 p-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-white shadow-sm">
                <FileText className="h-4 w-4 text-surface-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-surface-900">
                  {reports[0].title}
                </p>
                <p className="text-xs text-surface-500">
                  {reports[0].author} &middot;{reports[0].createdAt.slice(0, 10)}
                </p>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No document selected"
              icon={FileText}
              action={
                <Button variant="secondary" size="sm">
                  <FileText className="h-4 w-4" />
                  Browse Reports
                </Button>
              }
            />
          )}
        </SectionCard>

        {/* Right panel */}
        <SectionCard
          title="Document B"
          action={
            <Button variant="secondary" size="sm">
              <Plus className="h-4 w-4" />
              Select
            </Button>
          }
        >
          {reports[1] ? (
            <div className="flex items-center gap-3 rounded-lg border border-surface-100 bg-surface-50/50 p-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-white shadow-sm">
                <FileText className="h-4 w-4 text-surface-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-surface-900">
                  {reports[1].title}
                </p>
                <p className="text-xs text-surface-500">
                  {reports[1].author} &middot; {reports[1].createdAt.slice(0, 10)}
                </p>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No document selected"
              icon={FileText}
              action={
                <Button variant="secondary" size="sm">
                  <FileText className="h-4 w-4" />
                  Browse Reports
                </Button>
              }
            />
          )}
        </SectionCard>
      </div>

      {/* Comparison features */}
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Content Diff', desc: 'Compare text differences between documents' },
          { label: 'Statistics', desc: 'Compare metrics and data points' },
          { label: 'AI Analysis', desc: 'Get AI-powered comparison insights' },
        ].map((feature) => (
          <button
            key={feature.label}
            className="rounded-xl border border-surface-200 bg-white p-4 text-left shadow-sm transition-colors hover:border-primary-200 hover:bg-primary-50"
          >
            <p className="text-sm font-semibold text-surface-900">
              {feature.label}
            </p>
            <p className="mt-1 text-xs text-surface-500">{feature.desc}</p>
          </button>
        ))}
      </div>
    </PageContainer>
  )
}
